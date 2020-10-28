#!/usr/bin/env python
# -*- coding: utf8
# 
from datetime import datetime as DT, timedelta
import re
import logging

from libs import simple_tbl
#from .dbm_user import user


loger = logging.getLogger()

class attenders(simple_tbl):
	work_table = 'attenders'
	main_keys = ('aid', 'mid', 'mtimes', 'userid', 'wxuserid', 'username', 'roleid', 'signtime', 'remark', 'status')
	def_v = {'defv': '', 'roleid': 0, 'status': 0}
	pkey = 'aid'

	STA_NOTSIGN = 0 #未签到或未出席，默认值, 在会议过后相当于未出席
	STA_SIGNED = 1 #正常签到
	STA_LATE = 2 #迟到
	STA_OFF = 3 # 请假

	ROLE_MEMBER = 0
	ROLE_ASSIST = 1

	# mtimes(mcount): meeting times: 对于重复性会议，需要基于相同的mid建立新的参会名单

	create_syntax = """CREATE TABLE `{tbl_name}` (\
	`aid` INT NOT NULL AUTO_INCREMENT,\
	`mid` INT NOT NULL,\
	`mtimes` SMALLINT UNSIGNED DEFAULT 0,\
	`userid` VARCHAR(32) NOT NULL,\
	`wxuserid` VARCHAR(32),\
	`username` VARCHAR(12),\
	`roleid` INT DEFAULT 0,\
	`signtime` DATETIME,\
	`remark`  VARCHAR(256) DEFAULT "",\
	`status` TINYINT DEFAULT 0,\
	PRIMARY KEY (`aid`),\
	KEY `_mid` (`mid`),\
	KEY `_userid` (`userid`)\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""
	# roleid: == 1, assistance，可以修改会议

	# 个人
	@classmethod
	def sign(cls, mid, userid, meetingdtime, sign_pre, sign_limit, stime=None, mcount=0):
		# 签到
		# 根据会议参数判断是否迟到，是否可签到，返回状态, 本地不做跨表，因此需要传入参数
		# mcount: 默认为最近一次
		stime = cls._fixed_date(stime)
		_meetingdtime = cls._fixed_date(meetingdtime)
		_t_stime = stime.timestamp()
		_t_mtime = _meetingdtime.timestamp()
		_t_allow_start = _t_mtime - sign_pre * 60
		_t_allow_end = _t_mtime + sign_limit * 60
		sta = cls.STA_NOTSIGN
		if _t_stime < _t_allow_start:
			# too early to sign
			return _t_stime - _t_allow_start
		elif _t_stime > _t_allow_end:
			sta = cls.STA_LATE
		else:
			sta = cls.STA_SIGNED
		sqlcmd = 'UPDATE %s SET status=%d,signtime="%s" WHERE mid=%d AND userid="%s" AND mtimes=%s' % (cls.work_table, sta, stime, mid, userid, mcount)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def sign_status(cls, mid, userid, mcount=0):
		sqlcmd = 'SELECT aid,signtime,status FROM %s WHERE mid=%d AND userid="%s" AND mtimes=%d' % (cls.work_table, mid, userid, mcount)
		dbrt = cls._con_pool.query_db(sqlcmd, one=True)
		if dbrt:
			return {'aid': dbrt[0], 'signtime': dbrt[1], 'status': dbrt[2]}

	@classmethod
	def my_assists(cls, userid):
		return cls._con_pool.query_db('SELECT DISTINCT mid FROM %s WHERE userid="%s" AND roleid=%d' % (cls.work_table, userid, cls.ROLE_ASSIST), single=True)
		filterstr = 'userid="%s" AND roleid=%d' % (userid, cls.ROLE_ASSIST)
		get_columns = 'aid,mid,status'
		return cls._list_items(get_columns=get_columns, filterstr=filterstr)

	@classmethod
	def my_attends(cls, userid):
		sqlcmd = 'SELECT mid FROM %s WHERE userid="%s"'

	@classmethod
	def remark(cls, aid, remark):
		# 提交remark/memo
		return cls._single_mod(aid, 'remark', remark)

	# 管理
	@classmethod
	def get_attenders(cls, mid, mtimes=0, signmode=None, withremark=False):
		# 列出某个会议的预定参会人员表；
		# signmode：筛选某类签到人员
		# withremark: 是否包含人员remark
		# mtimes: 0-onetime meeting;; 
		if withremark:
			get_columns = 'aid,userid,username,roleid,signtime,remark,status'
		else:
			get_columns = 'aid,userid,username,roleid,signtime,status'
		filterstr = 'mid=%s AND mtimes=%s' % (mid, mtimes)
		if isinstance(signmode, int):
			filterstr += 'AND status=%d' % signmode
		return cls._list_items(get_columns=get_columns, filterstr=filterstr)

	@classmethod
	def wx_attender(cls, mid, mtimes=0):
		# 列出参会人员，仅wxuserid
		sqlcmd = 'SELECT wxuserid FROM %s WHERE mid=%s AND mtimes=%d AND wxuserid is not NULL' % (cls.work_table, mtimes, mid)
		return cls._con_pool.query_db(sqlcmd, single=True)

	@classmethod
	def set_attenders(cls, mid, users, mtimes=-1):
		# 创建参会人员名单，在会议开始前可操作；防止重复
		# param:
		# users: [{userid: {username, roleid}}]
		# get exists for conflicts
		# mtimes: meeting times
		if mtimes == -1:
			# auto for last recent
			mtimes = cls._con_pool.query_db('SELECT mtimes FROM %s WHERE mid=%d ORDER BY mtimes DESC LIMIT 1' % (cls.work_table, mid), one=True, single=True) or 0
		_currents = cls._con_pool.query_db('SELECT userid FROM %s WHERE mid=%d AND mtimes=%d' % (cls.work_table, mid, mtimes), single=True)
		if _currents:
			currents = set(_currents)
			legal_users = []
			for u in users:
				if u['userid'] in currents:
					loger.warning(f"exsits user when add attenders: {u['username']}")
				else:
					legal_users.append(u)
			if len(legal_users) == 0:
				return 0
		value_str = '('
		sqlcmd = 'INSERT INTO %s(mid,mtimes,userid,wxuserid,username,roleid) VALUES %s'
		value_str += '),('.join(['%s,%s,"%s","%s","%s",%s' % (mid, mtimes, u['userid'], u['wxuserid'], u['username'], u.get('roleid', 0)) for u in legal_users]) + ')'
		return cls._con_pool.execute_db(sqlcmd % (cls.work_table, value_str))

	@classmethod
	def copy_attenders(cls, mid, mtimes=0):
		# 重复性会议，将前一次的参会者名单复制一份，成为下一份名单
		# mtimes(mtimes): 指定会议的mtimes，则mtimes-1为上一次的mtimes; 未指定则按照第一次，mtimes=0
		# check:如果名单已经存在，则不进行操作
		pre_attenders = None
		cur_attenders = None
		cur_attenders = cls._con_pool.query_db('SELECT DISTINCT userid,wxuserid,username,roleid FROM %s WHERE mid=%s AND mtimes=%s' % (cls.work_table, mid, mtimes))
		if cur_attenders:
			loger.warning("cur_attender exists (%d)!" % len(cur_attenders))
			return
		if mtimes>0:
			pre_attenders = cls._con_pool.query_db('SELECT DISTINCT userid,wxuserid,username,roleid FROM %s WHERE mid=%s AND mtimes=%s' % (cls.work_table, mid, mtimes-1))
		if mtimes == 0 or pre_attenders is None:
			pre_attenders = cls._con_pool.query_db('SELECT DISTINCT userid,wxuserid,username,roleid FROM %s WHERE mid=%s AND mtimes=0' % (cls.work_table, mid))
			if pre_attenders:
				# 如果上次无参会者，则按照最初的用户复制
				mtimes += 1
		if pre_attenders:
			varray = []
			for a in pre_attenders:
				varray.append('(%s,%s,"%s","%s","%s",%s)' % (mid,mtimes,*a))
			sqlcmd = "INSERT INTO %s(mid,mtimes,userid,wxuserid,username,roleid) VALUES%s" % (cls.work_table, ",".join(varray))
			return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def set_assistor(cls, aid, unset=False):
		# aid means a mtimes
		if unset:
			return cls._single_mod(aid, 'roleid', 0)
		return cls._single_mod(aid, 'roleid', 1)

	@classmethod
	def kick(cls, aid):
		return cls._manage_item('delete', pkey=aid)
		
	@classmethod
	def remove(cls, mid, users):
		if isinstance(users, str):
			users = '"' + users.replace(",", '","') + '"'
		sqlcmd = 'DELETE FROM %s WHERE aid>0 and mid=%s and userid in (%s)' % (cls.work_table, mid, users)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def mark_attenders(cls, mid, userids, status=0):
		# 设置某些参会者的状态；
		# status=0，快速配置参会人员[增加 或 变更状态]
		users = ','.join(['"%s"' % uid for uid in userids])
		sqlcmd = 'UPDATE %s SET status=%d WHERE aid>0 and userid in (%s)' % (cls.work_table, status, users)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def drop_bymeeting(cls, mid, mcount=0):
		# 清除某个会议的所有参会人员，为删除会议的前置操作
		if mtimes == -1:
			# auto for last
			mtimes = cls._con_pool.query_db('SELECT mtimes FROM %s WHERE mid=%d ORDER BY mtimes DESC LIMIT 1' % (cls.work_table, mid), one=True, single=True)
		sqlcmd = 'DELETE FROM %s WHERE aid>0 AND mid=%d' % (cls.work_table, mid)
		if mcount >= 0:
			sqlcmd += ' AND mtimes=%s' % mcount
		return cls._con_pool.execute_db(sqlcmd)