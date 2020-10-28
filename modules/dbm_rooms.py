#!/usr/bin/env python
# -*- coding: utf8
# 
from datetime import datetime, timedelta
import re
import logging

from libs import simple_tbl

loger = logging.getLogger()

class mroom(simple_tbl):

	work_table = 'mrooms'
	main_keys = ('roomid', 'objid', 'name', 'room_identifier', 'sign_mode', 'location', 'building', 'floor', 'room_no', 'allow_people', 'next_meeting', 'next_mdtime', 'status')
	list_keys = 'roomid,objid,name,room_identifier,sign_mode,allow_people,next_meeting,next_mdtime,status'
	require_keys = 'objid,name,sign_mode'
	def_v = {'allow_people': 0, 'next_meeting': 0, 'status': 1}
	pkey = 'roomid'
	meeting_table = ''

	STA_CLOSED = -1 #(场地)不可用,人为关闭
	STA_READY = 1 #正常可用
	STA_WAITING = 10
	STA_MEETTING = 100

	SMODE_NO = 0
	SMODE_BT = 1
	SMODE_WIFI = 2
	SMODE_QRCODE = 4

	create_syntax = """CREATE TABLE `{tbl_name}` (\
    `roomid` INT NOT NULL AUTO_INCREMENT, \
    `objid` VARCHAR(32) NOT NULL, \
	`name` VARCHAR(16) NOT NULL, \
	`room_identifier` VARCHAR(36) DEFAULT "", \
	`sign_mode` TINYINT DEFAULT 0, \
	`location` VARCHAR(64) DEFAULT NULL, \
	`building` VARCHAR(12) DEFAULT NULL, \
	`floor` TINYINT DEFAULT 0, \
	`room_no` INT DEFAULT 0, \
	`allow_people` SMALLINT UNSIGNED DEFAULT 0, \
	`next_meeting` INT DEFAULT 0, \
	`next_mdtime` DATETIME, \
	`status` TINYINT DEFAULT 1, \
	PRIMARY KEY (`roomid`),\
	KEY `mkey` (`next_meeting`)\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""

	# room_identifier: 设备uuid； 设备major，设备minor, 或者WIFI签到时ssid

	@classmethod
	def new(cls, objid, params):
		if not any([_ in params for _ in ('name', 'sign_mode', 'room_identifier')]):
			raise ValueError("至少需要会议室名称")
		params['objid'] = objid
		return cls._manage_item('new', orign_data=params)

	def set_signer(cls, mode, identifed):
		if mode == cls.SMODE_NO:
			identifed = ""
		sqlcmd = 'UPDATE %s SET sign_mode=%d,room_identifier="%s"'
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def update(cls, roomid, **kwargs):
		# 变更，附上最近修改时间；lasttime
		if 'lasttime' not in kwargs:
			kwargs['lasttime'] = datetime.now()
		return cls._manage_item('modify', pkey=roomid, **kwargs)

	@classmethod		
	def lock(cls, roomid, unlock=False, force=False):
		# 关闭会议室；如果有安排会，则需要先修改对应会议的召开地点；
		# unlock: 修改为开放
		# 强制关闭则无视直接关闭
		# return True 才是成功
		if unlock:
			sqlcmd = "UPDATE %s SET status=%d WHERE roomid=%d" % (cls.work_table, cls.STA_READY, roomid)
			return cls._con_pool.execute_db(sqlcmd)
		if not force:
			nmid = cls._con_pool.query_db("SELECT mid FROM %s WHERE roomid=%d" % (cls.work_table, roomid), one=True)
			if nmid:
				loger.warning("meeting[%s] alive with room[%s]!" % (nmid[0], roomid))
				return nmid
		sqlcmd = "UPDATE %s SET status=%d WHERE roomid=%d" % (cls.work_table, cls.STA_CLOSED, roomid)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def set_next_auto(cls, roomid, mid, nextdtime):
		# compare the current next_mdtime and nextdtime;
		# update the earlier
		now = datetime.today()
		sqlcmd = 'UPDATE %s SET next_meeting=%s,next_mdtime="%s" WHERE roomid=%s AND (next_mdtime<"%s" OR next_mdtime>"%s")' % \
		(cls.work_table, mid, nextdtime, roomid, now, nextdtime)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def set_next(cls, roomid, mid, nextdtime):
		# if next_start_dtime <= now, return false
		nextdtime = cls._date_str(nextdtime)
		return cls._manage_item('modify', roomid=roomid, next_meeting=mid, next_mdtime=nextdtime)

	@classmethod
	def get_next(cls, roomid):
		# return (next_meeting_id, next_meeting_datetime)
		sqlcmd = "SELECT next_meeting,next_mdtime FROM %s WHERE roomid=%d" % (self.work_table, roomid)
		return cls._con_pool.query_db(sqlcmd, one=True)

	@classmethod
	def detail(cls, roomid):
		return cls._manage_item("get", roomid)

	@classmethod
	def availables(cls, objid=None, by_people_limit=0, bybuilding=None, by_sign_mode=None):
		# 列出满足一般条件的会议室：
		# 某个楼（设定buiding）；
		# 人数上限；
		filter_str = 'objid="%s" AND status>%s' % (objid, cls.STA_CLOSED) if objid else "status>%s" % cls.STA_CLOSED
		if by_people_limit > 0:
			filter_str += " AND (allow_people=0 OR allow_people>=%s)" % by_people_limit
		if bybuilding:
			filter_str += ' AND building="%s"' % bybuilding
		if by_sign_mode:
			filter_str += ' AND sign_mode=%s' % by_sign_mode
		dbrt = cls._list_items(get_columns=cls.list_keys, filterstr=filter_str, limit=100)
		return dbrt

	@classmethod
	def list(cls, objid, page, pagesize, lastid=0, takeall=False, summary=False):
		filterstr = 'objid="%s"' % objid
		if takeall is False:
			filterstr += ' AND status>%d' % cls.STA_CLOSED
		offset = (page - 1) * pagesize
		get_columns = 'roomid,name,room_identifier,sign_mode,location,allow_people,next_meeting,next_mdtime,status'
		if lastid > 0:
			return cls._list_items(lastid=lastid, get_columns=get_columns, limit=pagesize, filterstr=filterstr, summary=summary)
		else:
			return cls._list_items(get_columns=get_columns, limit=pagesize, offset=offset, filterstr=filterstr, summary=summary)
