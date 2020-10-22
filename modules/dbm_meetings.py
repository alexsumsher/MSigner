#!/usr/bin/env python
# -*- coding: utf8
# 
from datetime import datetime as DT, timedelta
import calendar
import re
import logging
import math

from libs import simple_tbl
from modules import mnode


loger = logging.getLogger()
""" 
关于日期时间：
# data from client is string-type-of datetime like: '2019-12-17T15:34:04.831926'(isoformat)(js: Date().toISOString():kick end Z)
# 注：转换（js isoformat 带时区的Z）：js端：(时区偏移+8小时为北京时间)
# c1 = Date().toISOString() = "2019-12-17T07:51:20.417Z" => 
# c1.replace(/T(\d{2})/, "T"+String(Number(RegExp.$1)+8).padStart(2)).substr(0,c1.length-1) => "2019-12-17T15:51:20.417"
#  '2019-12-17 15:34:04' or '2019/12/17 15:34:04' :
if isinstance(next_start_time, datetime):
	startdt = next_start_time
else:
	# 错误的日期文字格式; 可能为'2019-12-17 15:34:04' or '2019/12/17 15:34:04'
	try:
		startdt = datetime.fromisoformat(next_start_time)
	except ValueError:
		splits = re.findall(r'\d+', next_start_time)
		startdt = datetime(*[int(_) for _ in splits])
now = datetime.today()
if now >= startdt:
	# 开始时间在当前时间之前
	return False
"""
class meeting(simple_tbl):
	work_table = 'meetings'
	main_keys = ('mid', 'objid', 'name', 'holder', 'mroom', 'roomname', 'sign_mode', 'counting', 'lastetime', 'ondate', \
		'ontime', 'mtime', 'nextdtime', 'rpmode', 'rparg', 'sign_pre', 'sign_limit', 'p_start', 'p_end', 'status')
	list_keys = 'mid,objid,name,holder,mroom,roomname,sign_mode,counting,ondate,ontime,mtime,nextdtime,rpmode,rparg,sign_pre,sign_limit,p_start,p_end,status'
	require_keys = 'objid,name,holder'
	def_v = {'defv': '', 'mroom': 0, 'status': 0}
	pkey = 'mid'

	STA_WAITING = 0 # 正常，未开会
	STA_ONLINE = 1 # 正常，已开会（手动设置，未设置不影响）
	STA_FINISH = 2 # 正常，会议结束
	STA_CLOSED = -1 # 取消
	STA_OVERP = -10 # 周期性会议，阶段已经结束

	# Defined FROM mroom table
	SMODE_NO = 0
	SMODE_BT = 1
	SMODE_WIFI = 2

	MEETING_TIME = 120 # 默认会议时间
	PRE_ANNOUNCE_TIME = 30 # 默认提前时间（通知，可建立会议)
	# couting: 次数-当前（nextdtime-为第几次）

	# RMODES from mnode

	create_syntax = """CREATE TABLE `{tbl_name}` (\
    `mid` INT NOT NULL AUTO_INCREMENT, \
	`objid` VARCHAR(32) NOT NULL,\
	`name` VARCHAR(32) NOT NULL,\
	`holder` VARCHAR(32) NOT NULL,\
	`mroom` INT DEFAULT 0,\
	`roomname` VARCHAR(16) DEFAULT NULL,\
	`room_identifier` VARCHAR(36) DEFAULT NULL,\
	`sign_mode` TINYINT DEFAULT 0,\
	`counting` TINYINT UNSIGNED DEFAULT 0,\
	`lastetime` DATETIME, \
	`ondate` DATE,\
	`ontime` TIME,\
	`mtime` SMALLINT DEFAULT 120,\
	`nextdtime` DATETIME,\
	`rpmode` SMALLINT UNSIGNED DEFAULT 0,\
	`rparg` VARCHAR(32) ,\
	`sign_pre` SMALLINT UNSIGNED DEFAULT 10,\
	`sign_limit` SMALLINT UNSIGNED DEFAULT 30,\
	`p_start` DATETIME,\
	`p_end` DATETIME, \
	`status` TINYINT DEFAULT 0,\
	PRIMARY KEY (`mid`),\
	KEY `mkey` (`mroom`)\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""
	# holder: 默认为creator除非显式设定manager；assistance在member表中
	# sign_pre: 提前多少分钟可以签到
	# sign_limit：会议开始后多少分钟内允许签到
	# lastetime: last edit datetime
	# ondate: (next meeting) on which date; ontime: (next meeting) on times; mtime: meeting time by minutes
	# rpmode: repeat mode: repeatly meeting by ontime(0), week(1), month(2); rparg of 1,2,3... the date repeat
	# 注意：mroom 可以为0，表示未指定会议室，尤其对于周期性会议而言

	@classmethod
	def new(cls, objid, params):
		# 需要使用meeting
		ontime = params['ontime'] #string; '%H:%M:%S'
		rmode = int(params.get('rpmode', 0))
		now = DT.today()
		if rmode == mnode.RMODE_ONCE:
			# nextdtime = DT.strptime(ondate + " " + ontime, '%Y-%m-%d %H:%M')
			ondate = params['ondate'] #string; '%Y-%m-%d'
			nextdtime = cls._fixed_date(ondate + " " + ontime)
			delta = nextdtime - now
			if delta.days <0 or delta.seconds//60 < cls.PRE_ANNOUNCE_TIME:
				loger.error("ERROR: too late to create meeting!")
				return 0
			else:
				params['nextdtime'] = nextdtime
		else:
			rparg = params['rparg']
			if isinstance(rparg, (list,tuple)):
				rparg = ','.join(rparg)
				params['rparg'] = rparg
		if rmode not in mnode.RMODES:
			loger.error("WRONG meeting mode!")
			return 0
		params['objid'] = objid
		params['lastetime'] = now
		print(params)
		mid = cls._manage_item('new', orign_data=params)
		return mid

	@classmethod
	def delete(cls, mid, bymark=True):
		# 关闭或删除；
		# 关闭： 超出时间段的重复会议、会议结束的一次性会议
		if bymark:
			sqlcmd = "UPDATE %s SET status=%d WHERE mid=%d" % (cls.work_table, cls.STA_CLOSED, mid)
		else:
			sqlcmd = "DELETE FROM %s WHERE mid=%d" % (cls.work_table, mid)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def update(cls, mid=None, **kwargs):
		# 变更，附上最近修改时间；lasttime
		if mid is None and cls.pkey not in kwargs:
			#raise ValueError("need a primary key!")
			return False
		if mid:
			kwargs[cls.pkey] = int(mid)
		if 'lastetime' not in kwargs:
			kwargs['lastetime'] = DT.now()
		return cls._manage_item('modify', **kwargs)

	@classmethod
	def update_nextdtime(cls, mid, nextdtime, counting=0):
		if counting:
			sqlcmd = 'UPDATE %s SET counting=%s,nextdtime="%s",status=%d WHERE mid=%s' % (cls.work_table, counting, nextdtime, cls.STA_WAITING, mid)
		else:
			sqlcmd = 'UPDATE %s SET nextdtime="%s",status=%d WHERE mid=%s' % (cls.work_table, nextdtime, cls.STA_WAITING, mid)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def update_nextdtimes(cls, sequence, counting=0):
		# 更新nextdtime序列，用于将动态列表更新数据回写到数据库
		# sequence => list of mnode (mnode.update_sequence) v
		# sequence => [(mid, nextdtime), (mid, ndexdtime), ...] x
		# couting+=1
		sqlcmds = []
		if counting:
			sqlcmd = 'UPDATE %s SET counting={},nextdtime="%s" WHERE mid=%s'.format(counting)
		else:
			sqlcmd = 'UPDATE %s SET counting=counting+1,nextdtime="%s" WHERE mid=%s'
		for _node in sequence:
			# mnode
			sqlcmds.append(sqlcmd % (cls.work_table, _node.nextdtime, _node.mid))
		if sqlcmds:
			return cls._con_pool.do_sequence(sqlcmds)

	@classmethod
	def status(cls, mid, checkval=None):
		sta = cls._get_val(mid, 'status')
		if sta:
			if isinstance(checkval, int):
				return sta == checkval
			return sta

	@classmethod
	def detail(cls, mid):
		return cls._manage_item("get", mid)

	@classmethod
	def list_sp_meetings(cls, mids, simple=True):
		# mids: list of mid
		# usage: from queue, check_date
		get_columns = cls.list_keys if simple else None
		return cls._list_items(keyids=mids, get_columns=get_columns)

	@classmethod
	def list_by_objid(cls, objid, lastmid=0, page=0, pagesize=0, simple=False, summary=False):
		get_columns = cls.list_keys if simple else None
		filterstr = 'objid="%s"' % objid
		limit = pagesize or 50
		if lastmid:
			return cls._list_items(get_columns=get_columns, filterstr=filterstr, limit=limit, lastid=lastmid, summary=summary)
		offset = page * limit
		return cls._list_items(get_columns=get_columns, filterstr=filterstr, limit=limit, offset=offset, summary=summary)

	@classmethod
	def get_page(cls, size, objid=None):
		if objid:
			return math.ceil(cls._count())
		fstr = 'objid="%s"' % objid
		return math.ceil(cls._count(fstr))

	@classmethod
	def schedules_byday(cls, date=None):
		# 按日期筛会议
		# param: date: 
		date = date or DT.today().date()
		return cls._get_schedule_ondate(dates=[date])

	@classmethod
	def schedules_byweek(cls, week=None):
		# 按周筛会议
		# param: week: 1-n; by calendar; None as current week;
		if week is None or isinstance(week, DT):
			_t = DT.today() or week
			_t_weekday = _t.isoweekday()
			_t_from = _t - timedelta(days=_t_weekday)
			_t_end = _t + timedelta(days=(6 - _t_weekday))
		elif isinstance(week, int) and 0<=week<=6:
			_t = DT.today()
			try:
				week_dates =  calendar.Calendar(firstweekday=1).monthdatescalendar(_t.year, _t.month)[week]
			except IndexError:
				loger.error("WRONG index of week in month")
				return None
			_t_from = week_dates[0]
			_t_end = week_dates[-1]
		else:
			loger.error("Unkown week!")
			return None
		return cls._get_schedule_ondate(_t_from, _t_end)

	@classmethod
	def schedules_bymonth(cls, month=None):
		# 按月筛会议；
		# param: month: 1~12
		_t = DT.today()
		if not month:
			month = _t.month
		elif month <= 0 or month > 12:
			raise ValueError("Month Error!")
		month_dates =  calendar.Calendar(firstweekday=1).monthdatescalendar(_t.year, month)
		_t_from = month_dates[0][0]
		_t_end = month_dates[-1][-1]
		return cls._get_schedule_ondate(_t_from, _t_end)

	@classmethod
	def load_all_meetings(cls, workdt=None, bad_igore=True):
		# 加载所有的会议； 产生iter；返回list(*)
		# bad_ignore：跳过无效
		workdt = str(workdt or TD.today())[:19]
		offset = 0
		limit = 1000
		if bad_igore:
			sqlcmd = 'SELECT * FROM %s WHERE (rpmode=%d AND nextdtime>"%s" AND status>%d) OR (rpmode>%d AND status>%d AND p_end>"%s") ORDER BY objid LIMIT %d,%d' % \
			(cls.work_table, mnode.RMODE_ONCE, workdt, cls.STA_CLOSED, mnode.RMODE_ONCE, cls.STA_CLOSED, workdt, offset, limit)
		else:
			sqlcmd = 'SELECT * FROM %s ORDER BY objid LIMIT %d,%d' % (cls.work_table, offset, limit)
		while True:
			dbrt = cls._con_pool.query_db(sqlcmd)
			if not dbrt:
				break
			for meeting in dbrt:
				yield meeting
			if len(dbrt)<limit:
				break
			offset += limit

	@classmethod
	def _get_schedule_ondate(cls, date_from=None, date_end=None, dates=None):
		# params must be datetime
		if dates:
			if len(dates) == 1:
				sqlcmd = 'SELECT * FROM %s WHERE DATE(nextdtime)="%s"' % (cls.work_table, dates[0])
			else:
				dates = ','.join(['"%s"' % _d for _d in dates])
				sqlcmd = 'SELECT * FROM %s WHERE DATE(nextdtime) in (%s)' % (cls.work_table, dates)
		else:
			date_from = datefrom or datetime.today().replace(hour=0, minute=0, second=0)
			date_end = date_end or date_from.replace(hour=23, minute=59, second=59)
			sqlcmd = 'SELECT * FROM %s WHERE nextdtime>%s AND nextdtime<%s' % (cls.work_table, date_from, date_end)
		dbrt = cls._con_pool.query_db(sqlcmd)
		if dbrt:
			return cls.dict_list_4json(cls.main_keys, dbrt)