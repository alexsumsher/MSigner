from datetime import datetime as DT, timedelta
import re
import logging

from libs import Qer
from .dbm_member import attenders as ATTENDERS
from .dbm_rooms import mroom as MROOM
from .dbm_meetings import meeting as METTING

loger = logging.getLogger()
# functions cross table datas


class mix_actions(Qer):

	def __init__(self, obj):
		self.oid = oid
		super(mix_actions, self).__init__()
		self.con = cls._con_pool

	def user_meetings(self, from_date=None, to_date=None, detail=False):
		# meetings between dates
		if detail is False:
			get_cols = 'A.mid,A.name,A.room_identifier,A.roomname,A.nextdtime,A.sign_pre,A.sign_limit,A.status'
		else:
			get_cols = 'A.mid,A.name,A.mroom,A.room_identifier,A.roomname,A.ondate,A.ontime,A.mtime,A.nextdtime,A.rp_mode,A.rp_args,A.sign_pre,A.sign_limit,A.status'
		from_date = self._date_str(from_date, True)
		# 参考：
		# select A.projectnumber,B.name from (select projectnumber from t_project_contract where date(createdate)>"2019-10-10") as A inner join t_equipment B on A.projectnumber=B.itemnumber where B.deleted=1;
		# 方法2
		#'SELECT B.userid,{get_cols} FROM {tbl_attenders} B LEFT JOIN {tbl_meeting} A on B.mid=A.mid where B.userid="{userid}" AND DATE(A.nextdtime)>="{datefrom}" AND DATE(A.nextdtime)<="{dateto}"'
		if to_date is None:
			sqlcmd = 'SELECT %s FROM (SELECT * FROM %s WHERE oid="%s" AND DATE(A.nextdtime)=%s) AS A INNER JION %s AS B ON A.mid=B.mid WHERE B.userid="%s"' % \
			(get_cols, METTING.work_table, self.oid, from_date, ATTENDERS.work_table, uid)
		else:
			to_date = self._date_str(to_date, True)
			sqlcmd = 'SELECT %s FROM (SELECT * FROM %s WHERE oid="%s" AND DATE(A.nextdtime)>="%s" AND DATE(A.nextdtime)<="%s") AS A INNER JION %s AS B ON A.mid=B.mid WHERE B.userid="%s"' % \
			(get_cols, METTING.work_table, self.oid, from_date, to_date, ATTENDERS.work_table, uid)
		#sqlcmd = 'SELECT %s FROM %s AS A WHERE mid in (SELECT mid FROM %s WHERE oid="%s" AND DATE(nextdtime)=%s) AND userid=%s' % (get_cols, METTING.work_table, )
		dbrt = self.con.query_db(sqlcmd)
		if dbrt:
			return self.dict_list_4json(dbrt, get_cols)

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
