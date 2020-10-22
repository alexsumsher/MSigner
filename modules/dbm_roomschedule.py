from datetime import datetime as DT, timedelta
import calendar
import re
import logging
import math

from libs import simple_tbl
#from modules import mnode


loger = logging.getLogger()


# room schedules

class room_schedule(simple_tbl):

	work_table = "room_schedule"
	STA_DEFAULT = 0

	create_syntax = """CREATE TABLE `{tbl_name}` (\
    `sid` INT NOT NULL AUTO_INCREMENT,\
    `roomid` INT NOT NULL,\
    `mid` INT NOT NULL,\
    `ondate` DATE,\
    `time_begin` TIME,\
    `time_end` TIME,\
    `mtime` SMALLINT UNSIGNED,\
	`status` TINYINT DEFAULT 0,\
	PRIMARY KEY (`sid`)\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""

	main_keys = ('sid', 'roomid', 'mid', 'ondate', 'time_begin', 'time_end', 'mtime', 'status')


	@staticmethod
	def str_time_test(time_begin0, time_end0, time_begin1, time_end1):
		# 测试时间段的冲突，基于string-format-time
		_b0 = [int(_) for _ in time_begin0.split(":")]
		_e0 = [int(_) for _ in time_end0.split(":")]
		_b1 = [int(_) for _ in time_begin1.split(":")]
		_e1 = [int(_) for _ in time_end1.split(":")]
		b0 = _b0[0] * 60 + _b0[1]
		e0 = _e0[0] * 60 + _e0[1]
		b1 = _b1[0] * 60 + _b1[1]
		e1 = _e1[0] * 60 + _e1[1]
		return b0<b1<e0 or b0<e1<e0 or (b1<b0 and e1>e0)

	@staticmethod
	def str_time_min(timestr):
		_timelist = timestr.split(":")
		return int(_timelist[0]) * 60 + int(_timelist[1])

	@classmethod
	def room_schedule(cls, roomid, mid=0, period_from=None, period_end=None, limit=0, offset=0):
		# 某个会议室的时间总表
		# @params:
		# mid>0: 指定会议（某会议在某个会议室的时间总表）
		# period_from/period_end: string-of-date(YYYY-MM-DD), date for searching period
		fstr = 'roomid={}'.format(roomid)
		if mid > 0:
			fstr += ' AND mid={}'.format(mid)
		if period_from:
			fstr += ' AND ondate>="{}"'.format(period_from)
		if period_end:
			fstr += ' AND ondate<="{}"'.format(period_end)
		fstr += ' ORDER BY ondate'
		return cls._list_items(limit=limit, offset=offset, filterstr=fstr)

	@classmethod
	def rooms_schedule(cls, roomids:str, mid=0, period_from=None, period_end=None, limit=0, offset=0):
		# 部分会议室时间总表
		# @params:
		# roomids: string-in-list
		fstr = 'roomid in ({})'.format(roomid)
		if mid > 0:
			fstr += ' AND mid={}'.format(mid)
		if period_from:
			fstr += ' AND ondate>="{}"'.format(period_from)
		if period_end:
			fstr += ' AND ondate<="{}"'.format(period_end)
		fstr += ' ORDER BY ondate'
		return cls._list_items(limit=limit, offset=offset, filterstr=fstr)

	@classmethod
	def meeting_schedule(cls, mid, from_date=None, end_date=None, limit=0, offset=0):
		# 某个会议的时间总表
		# @params:
		# from_date/end_date: string-of-date(YYYY-MM-DD) 
		fstr = 'mid={}'.format(mid)
		if from_date:
			fstr += ' AND ondate>="{}"'.format(from_date)
		if end_date:
			fstr += ' AND ondate<="{}"'.format(end_date)
		fstr += ' ORDER BY ondate'
		return cls._list_items(limit=limit, offset=offset, filterstr=fstr)

	@classmethod
	def one_meeting(cls, roomid, mid, ondate, ontime, meetingtime=120):
		# 一次性会议时间表
		delta_h = meetingtime // 60
		delta_m = meetingtime % 60
		_h,_m,_s = [int(_) for _ in ontime.split(':')]
		endtime_h = _h + delta_h + (1 if delta_m + _m >= 60 else 0)
		endtime_m = (delta_m + _m) % 60
		endtime = '{:0=2d}:{:0=2d}:00'.format(endtime_h, endtime_m)
		params = {"roomid": roomid, "mid": mid, "ondate": ondate, "time_begin": ontime, "time_end": endtime, "mtime": meetingtime}
		return cls._manage_item("new", orign_data=params)

	@classmethod
	def repeatedly_meeting(cls, roomid, mid, date_list:list, ontime:str, meetingtime=120):
		# 建立基于某个会议-会议室的日期占用表[批量写入数据库]
		# @data_list: data-from mqueue-calendar-list [date-text]
		# ontime from mnode could be: string-in-time or {'hour': ontime[0], 'minute': ontime[1], 'second': 0, 'microsecond': 0}
		delta_h = meetingtime // 60
		delta_m = meetingtime % 60
		if isinstance(ontime, dict):
			ontime = '{:0=2d}:{:0=2d}:00'.format(ontime['hour'], ontime['minute'])
			endtime_h = ontime['hour'] + delta_h + (1 if delta_m + ontime['minute'] >= 60 else 0)
			endtime_m = (delta_m + ontime['minute']) % 60
		else:
			# ontime string: '00:00:00'
			_h,_m,_s = [int(_) for _ in ontime.split(':')]
			endtime_h = _h + delta_h + (1 if delta_m + _m >= 60 else 0)
			endtime_m = (delta_m + _m) % 60
		endtime = '{:0=2d}:{:0=2d}:00'.format(endtime_h, endtime_m)
		value_cmd = '({},{},"{}","{}","{}",{})'
		base_cmd = 'INSERT INTO %s(roomid,mid,ondate,time_begin,time_end,mtime) VALUES %s'
		value_cmds = []
		for d in date_list:
			value_cmds.append(value_cmd.format(roomid, mid, d, ontime, endtime, meetingtime))
		sqlcmd = base_cmd % (cls.work_table, ','.join(value_cmds))
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def meeting_schedule_change(cls, roomid, mid, date_list:list, ontime:str, meetingtime=120):
		# 变更某个重复性会议的日期表： 
		# 0）只变动会议室
		# 1）日期不变，只变动时间/时长
		# 2）日期变动
		# 全部存在可能的冲突
		pass

	@classmethod
	def single_meeting(cls, action, sid, **kwargs):
		# 修改一次性会议的时间表
		pass

	@classmethod
	def conflict_dtime(cls, roomid, test_date, time_begin, time_end=None, mtime=120):
		# 某个会议室在指定的时间段内是否存在冲突【针对一次性会议】
		# time_begin/time_end: 检测的冲突时间段
		if not time_end:
			# time_begin:str => time
			_tb = [int(_) for _ in time_begin.split(":")]
			time_end = "{:0=2d}:{:0=2d}:{:0=2d}".format(_tb[0]+mtime//60, _tb[1]+mtime%60, 0)
		query_cmd = 'SELECT sid,time_begin,time_end FROM %s WHERE roomid=%s AND ondate="%s" ORDER BY time_begin' % \
		(cls.work_table, roomid, test_date)
		test_times = cls._con_pool.query_db(query_cmd)
		if not test_times:
			return False
		time_begin_m = cls.str_time_min(time_begin)
		time_end_m = cls.str_time_min(time_end)
		t_s = t_e = 0
		for tt in test_times:
			# query TIME from db (auto transform) datetime.time: tt[1]
			# timedelta
			t_s = tt[1].seconds // 60
			t_e = tt[2].seconds // 60
			if time_begin_m<t_s<time_end_m or time_begin_m<t_e<time_end_m or \
			(t_s<time_begin_m and t_e>time_end_m):
				loger.warning(f"dtime conflict: {t_s}-{t_e}")
				return True

	@classmethod
	def conflict_schedule(cls, roomid, date_list:str, ontime:str, endtime=None, period_from=None, period_end=None, mtime=120):
		# params:
		# ontime/endtime: 会议开始的时间及终止时间
		if not endtime:
			# time_begin:str => time
			_tb = [int(_) for _ in ontime.split(":")]
			endtime = "{:0=2d}:{:0=2d}:{:0=2d}".format(_tb[0]+mtime//60, _tb[1]+mtime%60, 0)
		query_cmd = 'SELECT sid,ondate,time_begin,time_end FROM %s WHERE roomid=%s'
		if period_from:
			query_cmd += ' AND ondate>="%s"' % period_from
		if period_end:
			query_cmd += ' AND ondate<="%s"' % period_end
		query_cmd += ' LIMIT 0,9999'
		total_schedule = cls._con_pool.query_db(query_cmd % (cls.work_table, roomid))
		if not total_schedule:
			return False
		test_time_begin = cls.str_time_min(ontime)
		test_time_end = cls.str_time_min(endtime)
		# 策略：
		'''
		0）转换ontime为time_begin(m), time_end(m)
		1) 获取所有的（指定时间范围内的）会议时间表
		2）日期比对（2层循环），同日期则比对时间
		'''
		date_set = set(date_list)
		for row in total_schedule:
			if str(row[1]) in date_set:
				_time_begin = row[2].seconds // 60
				_time_end = row[3].seconds // 60
				if test_time_begin<=_time_begin<=test_time_end or test_time_begin<=_time_end<=test_time_end or \
				(_time_begin<test_time_begin and _time_end>test_time_end):
					loger.warning(f"rp conflict on: {row[1]}:{_time_begin}-{_time_end}")
					return True

	@classmethod
	def clearby_meeting(cls, mid, clear_all=False):
		# 清空某个（周期性）会议[批量变更数据库]，指定时间点之后的会议室占用：关闭会议后的操作
		# @params:
		# after_dtime: schedule of meeting after dtime should be remove
		# 已经开会过的不应该被移除（默认情况下），因此after_date None => 本日之后的
		if clear_all:
			sqlcmd = 'DELETE FROM %s WHERE sid>0 AND mid=%d' % (cls.work_table, mid)
		else:
			sqlcmd = 'DELETE FROM %s WHERE sid>0 AND mid=%d AND DATE(time_begin)>"%s"' % (cls.work_table, mid, DT.today().date())
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def clearby_room(cls, roomid, afterdate=None):
		pass

	@classmethod
	def update_on_1time(cls, to_roomid, mid, ondate, time_begin, time_end, sid=0, from_roomid=0, old_date=None):
		# 变更某次会议（一次性会议或重复性会议未来的某次会议）会议室/日期、时间
		# 需要明确给出会议的起始、终止时间进行冲突判断
		# 如果不明确给出sid，则必须给出old_date以查找
		if cls.conflict_dtime(to_roomid, ondate, time_begin, time_end):
			return False
		if sid:
			return cls._manage_item('modify', pkey=sid, roomid=to_roomid, ondate=ondate, time_begin=time_begin, time_end=time_end)
		sqlcmd = 'UPDATE %s SET roomid=%s,ondate="%s",time_begin="%s",time_end="%s" WHERE mid=%s AND ondate="%s"' % \
		(cls.work_table, to_roomid, ondate, time_begin, time_end, mid, old_date)
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def change_room(cls, to_roomid, mid, period_from=None, period_end=None):
		# 修改某个会议（一次或重复）在某个时间段内（针对重复性会议）的会议室，仅修改会议室
		# 从便捷性来说，应当在外部调用conflict_schedule函数进行判断，可行则操作，因此本函数不做冲突判断！
		sqlcmd = 'UPDATE %s SET roomid=%s WHERE mid=%s'
		if period_from:
			sqlcmd += ' AND ondate>="%s"' % period_from
		if period_end:
			sqlcmd += ' AND ondate<="%s"' % period_end
		return cls._con_pool.execute_db(sqlcmd)


if __name__ == '__main__':
	from libs import emptyCon
	E = emptyCon()
	Qer.set_con_pool(E)
	room_schedule.repeatedly_meeting(1, 1, ['2020-01-01', '2020-02-01', '2020-03-01'], '00:00:00')