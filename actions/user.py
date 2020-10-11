from datetime import datetime as DT, timedelta
import re
import logging

from libs import Qer
from modules import attenders as ATTENDERS, mroom as MROOM, meeting as METTING, user_tbl as USERS
from modules import mnode, Mqueue

loger = logging.getLogger()

# FROM USER SIDE: date is string;
class user_actions(Qer):

	@classmethod
	def login(cls, objid, userpwd, openid, userid="", username=""):
		if userid:
			sqlcmd = 'SELECT userid,openid,password FROM %s WHERE userid="%s" AND objid="%s" AND status>0 LIMIT 1' % (USERS.work_table, userid, objid)
		elif username:
			sqlcmd = 'SELECT userid,openid,password FROM %s WHERE username="%s" AND objid="%s" AND status>0 LIMIT 1' % (USERS.work_table, username, objid)
		else:
			return
		dbrt = cls._con_pool.query_db(sqlcmd, one=True)
		print(dbrt)
		if dbrt and dbrt[2] == userpwd and dbrt[1] == openid:
			u = cls(objid)
			u.extdata = dbrt[0]
			return u

	def __init__(self, objid, session=None):
		self.objid = objid
		self.session = session
		self.extdata = ""
		self.exceptinfo = None
		super(user_actions, self).__init__()
		self.con = self.__class__._con_pool

	# 用户需要参加的会议
	def user_meetings(self, userid, from_date=None, to_date=None, detail=False, for_mange=False):
		# meetings between dates
		# export users role
		if detail is False:
			get_cols = 'A.mid,A.name,A.sign_mode,A.counting,A.roomname,A.nextdtime,A.sign_pre,A.sign_limit,R.room_identifier,B.roleid,B.signtime,B.status'
		else:
			get_cols = 'A.mid,A.name,A.sign_mode,A.counting,A.mroom,A.roomname,A.ondate,A.ontime,A.mtime,A.nextdtime,A.rp_mode,A.rp_args,A.sign_pre,A.sign_limit,R.room_identifier,B.signtime,B.roleid,B.status'
		from_date = self._date_str(from_date, True)
		# 参考：
		# select A.projectnumber,B.name from (select projectnumber from t_project_contract where date(createdate)>"2019-10-10") as A inner join t_equipment B on A.projectnumber=B.itemnumber where B.deleted=1;
		# 方法2
		#'SELECT B.userid,{get_cols} FROM {tbl_attenders} B LEFT JOIN {tbl_meeting} A on B.mid=A.mid where B.userid="{userid}" AND DATE(A.nextdtime)>="{datefrom}" AND DATE(A.nextdtime)<="{dateto}"'
		if to_date is None:
			sqlcmd = 'SELECT %s FROM %s A LEFT JOIN %s R ON A.mroom=R.roomid LEFT JOIN %s B ON A.mid=B.mid WHERE A.objid="%s" AND DATE(A.nextdtime)="%s" AND A.status>=0 AND B.mtimes=A.counting AND B.userid="%s"' % \
			(get_cols, METTING.work_table, MROOM.work_table, ATTENDERS.work_table, self.objid, from_date, userid)
		else:
			to_date = self._date_str(to_date, True)
			sqlcmd = 'SELECT %s FROM %s A LEFT JOIN %s R ON A.mroom=R.roomid LEFT JOIN %s B ON A.mid=B.mid WHERE A.objid="%s" AND DATE(A.nextdtime)>="%s" AND DATE(A.nextdtime)<="%s" AND A.status>=0 AND B.mtimes=A.counting AND B.userid="%s"' % \
			(get_cols, METTING.work_table, MROOM.work_table, ATTENDERS.work_table, self.objid, from_date, to_date, userid)
		#sqlcmd = 'SELECT %s FROM %s AS A WHERE mid in (SELECT mid FROM %s WHERE objid="%s" AND DATE(nextdtime)=%s) AND userid=%s' % (get_cols, METTING.work_table, )
		if for_mange:
			sqlcmd += ' AND B.roleid>0'
		sqlcmd += ' ORDER BY A.nextdtime'
		dbrt = self.con.query_db(sqlcmd)
		if dbrt:
			fields = get_cols.replace('A.', '').replace('B.', '').replace('R.', '')
			return self.dict_list_4json(dbrt, fields)

	def secure_sign(self, userid, mid, roomid, identify_key, stime=None):
		# 安全签到，服务器端认证
		# params：identify_key: 传入识别序号
		check_sql = 'SELECT sign_mode,room_identifier FROM %s WHERE roomid=%s' % (MROOM.work_table, roomid)
		dbrt = self.con_pool.query_db(check_sql, one=True)
		if not dbrt:
			loger.error("room by roomid[%s] is not found!" % roomid)
			return
		# return None means error; True as success; False as failure
		_smode, _ident = dbrt[0]
		if _smode != MROOM.SMODE_NO and _ident != identify_key:
			loger.info("a wrong sign in by user[%s] to mid[%s] and roomid[%s] with identify_key[%s]!" % (userid, mid, roomid, identify_key))
			return False
		# check time and set status
		stime = self._fixed_date(stime)
		minfo = METTING._vget(mid, 'nextdtime,sign_pre,sign_limit', cols=3)
		if not minfo:
			loger.error("meeting not found with mid: %s" % mid)
			return False
		return ATTENDERS.sign(mid, userid, minfo[0], minfo[1], minfo[2], stime=stime)

	def meeting_signin(self, userid, mid, identify_key, roomid=None, stime=None, mcount=-1):
		stime = stime or DT.now()
		mqueue = Mqueue.get_queue(self.objid)
		_meeting = mqueue[mid]
		if not _meeting:
			self.extdata = '未找到对应的会议'
			return False
		print(_meeting,_meeting.mroom)
		_roomid = _meeting.mroom or METTING._vget(mid, 'mroom')
		if roomid and _roomid != roomid:
			self.extdata = '签到会议室和开会会议室不匹配'
			return False
		else:
			roomid = _roomid
		if not roomid:
			self.extdata = '找不到对应的会议室'
			return False
		if mcount == -1:
			mcount = _meeting.counting
		sign_pre,sign_limit = METTING._vget(mid, 'sign_pre,sign_limit', cols=2)
		#pre_sec = minfo[0] * 60
		#limit_sec = minfo[1] * 60
		#delta = stime - _meeting_time
		#if (delta.days == -1 and (24 * 60 *60 - delta.seconds < pre_sec)) or (delta.days == 0 and delta.seconds < limit_sec):
		#	return ATTENDERS.sign(mid, userid, minfo[0], minfo[1], minfo[2], stime=stime)
		#return False
		rt = ATTENDERS.sign(mid, userid, _meeting.nextdtime, sign_pre, sign_limit, stime=stime, mcount=mcount)
		if isinstance(rt, float) and rt < 0:
			self.extdata = '未到签到时间'
			return False
		elif rt:
			return True
		else:
			self.extdata = '签到失败'
			return False

	def meeting_off(self, userid, mid, mcount=-1, remark=None):
		mqueue = Mqueue.get_queue(self.objid)
		_meeting = mqueue[mid]
		if not _meeting:
			# no meeting; one time meeting and overtime;
			return False
		now = DT.now()
		if (_meeting.nextdtime - now).days < 0:
			self.extdata = "会议已经开始；非可请假时间"
		if mcount == -1 or mcount is None:
			mcount = _meeting.counting
		sqlcmd = 'UPDATE %s SET status=%d,remark="%s" WHERE mid=%d AND userid="%s" AND mtimes=%d' % \
		(ATTENDERS.work_table, ATTENDERS.STA_OFF, remark or "", mid, userid, mcount)
		return ATTENDERS._con_pool.execute_db(sqlcmd)

	def today_next_meeting(self, userid, dtime=None):
		# 用户在指定时间点之后的，当日最近一次会议；
		# 不建议服务器端执行，用户登录后直接获取自己的当日会议列表，由客户端直接筛选列出来；
		dtime = dtime or DT.now()
		date = dtime.date()
		mqueue = Mqueue.get_queue(self.objid)
		today_meetings = mqueue.today(date)
		if today_meetings.length == 0:
			return 0
		# get list of mids of user from db, check in today_meetings(sorted) for the first one
		today_meetings_str = ','.join([str(i) for i in today_meetings])
		sqlcmd = 'SELECT mid FROM %s WHERE mid in (%s) AND userid="%s"' % (ATTENDERS.work_table, today_meetings_str, userid)
		#sqlcmd2 = 'SELECT A.mid FROM %s AS A LEFT JION %s AS B ON A.mid=B.mid WHERE A.mid in (%s) AND A.userid="%s" AND B.status>=0' % \
		#(ATTENDERS.work_table, METTING.work_table, today_meetings_str, userid)
		user_mids = self.con.query_db(sqlcmd, single=True)
		mid = 0
		if user_mids:
			for m in user_mids:
				if m in today_meetings:
					mid = m
					break
		#if mid > 0:
		#	return METTING.detail(mid)
		return mid

	def myschool(self, userid, objid=None):
		if objid:
			sqlcmd = 'SELECT title FROM sysconsts WHERE type="schools" AND ikey="%s"' % objid
		else:
			sqlcmd = 'SELECT title FROM sysconsts WHERE type="schools" AND ikey=(SELECT objid FROM users WHERE userid="%s")' % userid
		dbrt = self.con.query_db(sqlcmd, one=True)
		if dbrt:
			return dbrt[0]

			