from datetime import datetime as DT, timedelta
import calendar
import re
import logging
import math

from libs import simple_tbl
from modules import mnode


loger = logging.getLogger()


# room schedules

class room_schedule(simple_tbl):

	work_table = "room_schedule"

	create_syntax = """CREATE TABLE `{tbl_name}` (\
    `sid` INT NOT NULL AUTO_INCREMENT,\
    `roomid` INT NOT NULL,\
    `mid` INT NOT NULL,\
    `from_dtime` DATETIME,\
    `end_dtime` DATETIME,\
	`status` TINYINT DEFAULT 0,\
	PRIMARY KEY (`sid`),\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""

	main_keys = ('sid', 'roomid', 'mid', 'fro_dtime', 'end_dtime', 'status')


	@classmethod
	def room_schedule(cls, roomid, from_date=None, end_date=None):
		# 某个会议室的时间总表
		pass

	@classmethod
	def repeatedly_meeting(cls, roomid, mid, date_list, meetingtime=120):
		# 建立基于某个会议-会议室的日期占用表[批量写入数据库]
		# @data_list: data-from mqueue-calendar-list [date-text]
		value_cmds = ''
		base_cmd = 'INSERT INTO %s(roomid,mid,from_date,end_date) VALUES(%s)'

	@classmethod
	def rooms_schedule(cls, roomids, from_date=None, end_date=None):
		# 部分会议室时间总表
		pass

	@classmethod
	def conflict(cls, roomid, from_dtime, end_dtime):
		# 某个会议室在某个时间段内是否存在冲突
		pass

	@classmethod
	def clearby_meeting(cls, mid, after_date=None):
		# 清空某个（周期性）会议[批量变更数据库]，指定时间点之后的会议室占用：关闭会议后的操作
		# @params:
		# after_dtime: schedule of meeting after dtime should be remove
		# 已经开会过的不应该被移除（默认情况下），因此after_date None => 本日之后的
		after_date = after_date or DT.today().date()
		sqlcmd = 'DELETE FROM %s WHERE sid>0 AND mid=%d AND DATE(from_dtime)>"%s"' % (cls.work_table, mid, after_date)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def switch_room(cls, mid, roomid, after_date=None, from_dtime=None, end_dtime=None):
		# 将某个会议的所有（指定日期之后）的会议室进行变更[批量变更数据库]
		# @params
		# @after_date: 指定日期之后，None为所有
		# @from_dtime/end_dtime: 同时修正会议时间【起始/终止】
		pass