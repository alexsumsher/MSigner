from datetime import datetime as DT, timedelta
import re
import logging

from libs import Qer
from modules import attenders as ATTENDERS, mroom as MROOM, meeting as MEETING, user_tbl as USER
from modules import Mqueue, mnode
from tschool import myschool, pmsgr

loger = logging.getLogger()

# FROM USER SIDE: date is string;
class mgr_actions(Qer):
	limits = {
		'meeting_modify': 30, # 会议开始前30分钟可修改
		'meeting_drop': 0, # 会议开始后不可删除
	}


	@classmethod
	def action_ontime(cls, objid, mid, ondtime=None, mcount=0):
		# 确认当前对某个会议进行操作在时间上是否可行
		# 会议开始前30分钟不可变更。
		# mcount: 当明确给出mcount>0的数值，才会进行对应的比较
		m_limit = cls.limits['meeting_modify'] * 60
		meeting = Mqueue.get_queue(objid)[mid]
		if not meeting:
			loger.warning("mnode with id: %s not found!" % mid)
			return
		if mcount > 0 and mcount < meeting.counting:
			loger.warning("metting[%d] with counting[%d] overtime!" % (mid, mcount))
			return
		if meeting.status == mnode.STA_IDLE:
			return True
		ondtime = ondtime or DT.now()
		delta = meeting.nextdtime - ondtime
		return delta.days > 0 or (delta.days == 0 and delta.seconds > m_limit)

	@classmethod
	def _test_ctime(cls, ondate, ontime=None):
		# 判断会议的建立在时间上是否可行（一次性会议）
		nextdtime = cls._fixed_date(ondate + " " + ontime)
		delta = nextdtime - now
		return delta.days >= 0 and delta.seconds//60 > cls.PRE_ANNOUNCE_TIME

	@classmethod
	def is_manager(cls, userid, mid):
		# is holder or rolid==1
		sqlcmd = 'SELECT count(*) FROM %s WHERE mid=%s AND holder="%s"'
		c = self.con.query_db(sqlcmd, one=True)
		if not c:
			sqlcmd = 'SELECT count(*) FROM %s WHERE mid=%s AND userid="%s" AND rolid=%d' % (ATTENDERS.work_table, mid, userid, ATTENDERS.ROLE_ASSIST)
			c = self.con.query_db(sqlcmd, one=True)
			if not c:
				return False
		return True

	def __init__(self, objid, session=None):
		self.objid = objid
		self.session = session
		# extdata: store extend data if require
		# except_info: store exception infomations
		self.extdata = None
		self.except_info = None
		self.emsg = ""
		super(mgr_actions, self).__init__()
		self.con = self.__class__._con_pool

	def _time_conflict(self, ontime, mtime, t_s, t_e):
		# return True if conflict
		if isinstance(ontime, str):
			_tsplit = [int(_) for _ in ontime[:5].split(':')]
			_ts = _tsplit[0] * 60 + _tsplit[1]
		else:
			_ts = ontime.hour * 60 + ontime.minute
		_te = _ts + mtime
		return t_s<_ts<t_e or t_s<_te<t_e

	########## ======================================================================================================== ##########
	########## ================================================ FOR SCHOOL ============================================= ##########
	########## ======================================================================================================== ##########
	def import_all(self):
		return 0

	########## ======================================================================================================== ##########
	########## =============================================== ON MROOMS ===================+========================== ##########
	########## ======================================================================================================== ##########

	def available_rooms(self, ondate, ontime=None, mtime=120, by_sign_mode=None):
		# 在指定的日期/时间段内空闲（无会议）的会议室;
		# 对于重复性的无效
		if not ondate:
			return MROOM.availables(objid=self.objid, by_sign_mode=by_sign_mode)
		ondate = self._date_str(ondate, onlydate=True)
		if ontime is None:
			# room free all day long
			if by_sign_mode and by_sign_mode >= 0:
				sqlcmd = 'SELECT %s FROM %s WHERE objid="%s" AND sign_mode=%s AND roomid NOT IN (SELECT mroom FROM %s WHERE objid="%s" AND status>%d AND DATE(nextdtime) != "%s")' %\
				(MROOM.list_keys, MROOM.work_table, self.objid, by_sign_mode, MEETING.work_table, self.objid, MEETING.STA_CLOSED, ondate)
			else:
				sqlcmd = 'SELECT %s FROM %s WHERE objid="%s" AND roomid NOT IN (SELECT mroom FROM %s WHERE objid="%s" AND status>%d AND DATE(nextdtime) != "%s")' %\
				(MROOM.list_keys, MROOM.work_table, self.objid, MEETING.work_table, self.objid, MEETING.STA_CLOSED, ondate)
			dbrt = self.con.query_db(sqlcmd)
			if dbrt:
				return self.dict_list_4json(dbrt, MROOM.list_keys)
			else:
				return None
		get_columns = 'mid,name,mtime,nextdtime'
		sqlcmd = 'SELECT %s FROM %s WHERE objid="%s" AND status>%d AND DATE(nextdtime)="%s" ORDER BY mroom' % \
		(get_columns, MEETING.work_table, self.objid, MEETING.STA_CLOSED, ondate)
		dbrt = self.con.query_db(sqlcmd)
		if not dbrt:
			# no meeting on date, so all available
			return MROOM.availables(objid=self.objid, by_sign_mode=by_sign_mode)
		conflicts = []
		time_split = [int(_) for _ in ontime.split(':')]
		t_s = time_split[0]*60 + time_split[1]
		t_e = t_s + mtime
		for m in dbrt:
			if self._time_conflict(m[3], m[2], t_s, t_e):
				conflicts.append(str(m[0]))
		if len(conflicts) == 0:
			return MROOM.availables(objid=self.objid, by_sign_mode=by_sign_mode)
		else:
			filterstr = 'objid="%s" AND status>%d AND roomid NOT IN (%s)' % \
			(self.objid, MROOM.STA_CLOSED, ','.join(conflicts))
			return MROOM._list_items(get_columns=MROOM.list_keys, filterstr=filterstr, limit=100)

	def room_schedule(self, roomid, ondate, ontime, mtime=120, check_conflic=False):
		# 某个会议室的会议日程时间表 按日查询
		# check_dtime/check_mtime: 查询是否冲突; check_dtime: datetime
		ondate = self._date_str(ondate, True)
		get_cols = 'mid,name,mtime,nextdtime'
		sqlcmd = 'SELECT %s FROM %s WHERE mroom=%s AND status>%d AND DATE(nextdtime)="%s" ORDER BY nextdtime' % (get_cols, MEETING.work_table, roomid, MEETING.STA_CLOSED, ondate)
		dbrt = self.con.query_db(sqlcmd)
		if not dbrt:
			return None
		# export room schedule:
		if not check_conflic:
			return self.dict_list_4json(dbrt, get_cols)
		# 检测时间冲突(isconflic)，冲突则返回mid,否则0
		#check_dtime = self._fixed_date(check_dtime)
		dbrt = list(dbrt)
		dbrt.sort(key=lambda x:x[3])
		time_split = [int(_) for _ in ontime.split(':')]
		t_s = time_split[0]*60 + time_split[1]
		t_e = t_s + mtime
		for meeting in dbrt:
			if self._time_conflict(meeting[3], meeting[2], t_s, t_e):
				return meeting[0]
		return 0

	def room_close_safe(self, roomid, unlock=False):
		if unlock:
			sqlcmd = "UPDATE %s SET status=%d WHERE roomid=%d" % (self.tbl_room, mroom.STA_READY, roomid)
			return self.con.execute_db(sqlcmd)
		if not force:
			dbrt = self.con.query_db("SELECT A.mid,B.status FROM %s A LEFT JOIN %s B ON A.mid=B.mid WHERE A.roomid=%d" % (self.tbl_room, self.tbl_meeting, roomid))
			if dbrt and dbrt[1] >= 0:
				loger.warning("meeting[%s] alive with room[%s]!" % (dbrt[0], dbrt[1]))
				return dbrt[1]
		if lockuntil:
			sqlcmd = "UPDATE %s SET next_start_time=%s,status=%d WHERE roomid=%d" % (self.tbl_room, lockuntil, mroom.STA_CLOSED, roomid)
		else:
			sqlcmd = "UPDATE %s SET status=%d WHERE roomid=%d" % (self.tbl_room, mroom.STA_CLOSED, roomid)
		return self.con.execute_db(sqlcmd)

	########## ======================================================================================================== ##########
	########## =============================================== ON MEETINGS ============================================ ##########
	########## ======================================================================================================== ##########
	def newmeeting_safe(self, params, autonode=True, getndtime=False):
		# return int: -n | 0 | n;
		# ==> v2: return int,nextdtime
		# 0: cannot create node or insert to db
		# -n: conflict with meeting mid = n
		# n: success create meeting with mid = n
		roomid = int(params['mroom'])
		mname = params.get('name')
		_rpmode = int(params['rpmode'])
		_ondate = params.get('ondate')
		_ontime = params['ontime']
		_mtime = int(params['mtime'])
		# with roomid, precheck
		# precheck room
		if roomid > 0:
			if _rpmode == mnode.RMODE_ONCE:
				x_mid = Mqueue.get_queue(self.objid).filter_room_conflict_once(roomid, _ondate, _ontime, _mtime)
			else:
				_rparg = [int(_) for _ in params['rparg'].split(',')]
				_p_start = params['p_start']
				_p_end = params['p_end']
				x_mid = Mqueue.get_queue(self.objid).filter_room_conflict(_rpmode, _rparg, roomid, _ontime, _mtime, _p_start, _p_end)
			if x_mid > 0:
				loger.error("create meeting but conflic with meeting[%d]" % x_mid)
				return -x_mid
		# if no room or no conflict....
		if not (_rpmode == mnode.RMODE_ONCE and self._test_ctime(_ondate, _ontime)):
			loger.error("not allow time")
			self.emsg = "非许可时间"
			return 0
		try:
			if _rpmode == mnode.RMODE_ONCE:
				_node = mnode(0, mname, mroom=roomid, rpmode=_rpmode, ondate=_ondate, ontime=_ontime, mtime=_mtime)
			else:
				_rparg = [int(_) for _ in params['rparg'].split(',')]
				_p_start = params['p_start']
				_p_end = params['p_end']
				# counting=0
				_node = mnode(0, mname, mroom=roomid, rpmode=_rpmode, rparg=_rparg, ontime=_ontime, mtime=_mtime, p_start=_p_start, p_end=_p_end)
				# for first create new, nextdtime aouto make by node, put with params
				params['nextdtime'] = _node.nextdtime
		except ValueError:
			loger.error("create node wrong with params: [%s]" % params)
			return 0
		mid = MEETING.new(self.objid, params)
		if mid > 0:
			_node.mid = mid
			Mqueue.auto_node(self.objid, _node)
			if getndtime:
				self.extdata = _node.nextdtime
			return mid
		return 0

	def drop_meeting(self, mid, attenders=False, force=False):
		# delete a meeting and clear attender and remove from mqueue
		step = 1
		rt = MEETING.delete(mid, bymark=not force)
		if not rt:
			loger.error("DROP_MEETING(%s): failure when delete from meeting." % mid)
			self.emsg = "数据库中不存在"
			return
		step = 2
		if attenders or force:
			rt = ATTENDERS.drop_bymeeting(mid)
			if not rt:
				self.emsg = "删除成员失败"
				loger.error("DROP_MEETING(%s): failure when clear attenders. but still continue." % mid)
		step = 3
		_mqueue = Mqueue.get_queue(self.objid)
		rt = _mqueue.remove(mid)
		if rt is True:
			loger.info("DROP_MEETING(%s): success.")
			MEETING.delete(mid, bymark=False)
		else:
			loger.error("DROP_MEETING(%s): failure when remove from queque!")
		return rt

	def fullmeeting(self, mid):
		# mroom maybe 0: 未指定会议室
		sqlcmd = 'SELECT M.*,R.room_identifier,R.sign_mode,R.allow_people FROM %s M LEFT JOIN %s R ON M.mroom=R.roomid WHERE mid=%s' % \
		(MEETING.work_table, MROOM.work_table, mid)
		take_columns = ','.join(MEETING.main_keys) + ',' + 'room_identifier,sign_mode,allow_people'
		dbrt = self.con.query_db(sqlcmd, one=True)
		return self.dict_list_4json(dbrt, take_columns, one=True)

	def update_ontime(self, mid, formdata):
		if not action_ontime(self.objid, mid):
			return
		meeting = Mqueue.get_queue(self.objid)[mid]
		for k,v in formdata.items():
			meeting[k] = v
		MEETING._manage_item('modify', **formdata)
		return  True
	########## ======================================================================================================== ##########
	########## ================================================ FOR USERS ============================================= ##########
	########## ======================================================================================================== ##########
	def set_attenders_bydp(self, depid):
		pass

	def list_attenders(self, mid, mcount=-1):
		mqueue = Mqueue.get_queue(self.objid)
		_meeting = mqueue[mid]
		if not _meeting:
			return ATTENDERS.get_attenders(mid)
		if mcount == -1:
			mcount = _meeting.counting
		return ATTENDERS.get_attenders(mid, mtimes=mcount)
	#
	def list_meetings(self, holder=None, page=1, size=20, summary=False):
		limit = size
		offset = (page - 1) * size
		take_columns = MEETING.list_keys + ',roomname'
		colums_m = 'M.' + MEETING.list_keys.replace(",", ",M.")
		colums_r = "R.name"
		wstr = 'M.objid="%s"' % self.objid if holder == 0 else 'M.objid="%s" AND M.holder="%s"' % (self.objid, holder)
		sqlcmd = 'SELECT %s,%s FROM %s AS M LEFT JOIN %s AS R ON M.mroom=R.roomid WHERE %s LIMIT %s,%s' % \
		(colums_m, colums_r, MEETING.work_table, MROOM.work_table, wstr, offset, limit)
		if holder:
			sqlcmd += ' AND M.holder="%s"'
		dbrt = self.con.query_db(sqlcmd)
		if dbrt:
			rtdata = self.dict_list_4json(dbrt, take_columns)
			if summary:
				wstr = 'objid="%s"' % self.objid if holder == 0 else 'objid="%s" AND holder="%s"' % (self.objid, holder)
				count = self.con.query_db('SELECT count(*) FROM %s WHERE %s' % (MEETING.work_table, wstr))
				return count,rtdata
			return rtdata
		return 0,None if summary else None

	def list_meetings2(self, rpmode=-1, p_start=None, p_end=None, holder=None, page=1, size=20, summary=False, overtime=True):
		# 完整的筛选显示：
		# rpmode: 0, 1,2对应各自类型，>0为周期性(传入12), -1:默认，不作为判断即全部
		# holder > 0: just for holders
		limit = size
		offset = (page - 1) * size
		warray = ['objid="%s"' % self.objid]
		assists_meetings = None
		if holder:
			# get assists list
			assists_meetings = ATTENDERS.my_assists(holder)
			warray.append('holder="%s"' % holder)
		if rpmode != -1:
			if rpmode in mnode.RMODES:
				warray.append('rpmode=%d' % rpmode)
			elif rpmode == 12:
				warray.append('rpmode>0')
		if p_start:
			warray.append('nextdtime>"%s"' % p_start)
		if p_end:
			warray.append('nextdtime<"%s"' % p_end)
		if overtime is False:
			warray.append('date(nextdtime)>="%s"' % DT.today().date())
		wstr = ' AND '.join(warray)
		if holder and assists_meetings:
			wstr = '(%s) OR (mid in %s)' % (wstr, str(tuple(assists_meetings)))
		if summary:
			count_cmd = 'SELECT count(*) FROM %s WHERE %s' % (MEETING.work_table, wstr)
			count = self.con.query_db(count_cmd, one=True)
			if not count or count[0] == 0:
				self.extdata = 0
				return None
			self.extdata = count[0]
		#wstr = 'M.objid="%s"' % self.objid if holder == 0 else 'M.objid="%s" AND M.holder=%d' % (self.objid, holder)
		sqlcmd = 'SELECT %s FROM %s WHERE %s LIMIT %s,%s' % (MEETING.list_keys, MEETING.work_table, wstr, offset, limit)
		dbrt = self.con.query_db(sqlcmd)
		if dbrt:
			return self.dict_list_4json(dbrt, MEETING.list_keys)

	def reset_status(self, aid):
		return ATTENDERS._single_mod(aid, 'status', ATTENDERS.STA_NOTSIGN)

	def sign_report(self, mid):
		# 会议参与签到记录
		pass