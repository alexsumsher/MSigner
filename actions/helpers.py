from datetime import datetime as DT, timedelta
import logging
from threading import Thread

from modules import meeting as METTING, attenders as ATTENDERS, mroom as MROOM
from modules import mnode
from tschool import app_school, pmsgr

loger = logging.getLogger()
# functions cross table datas

# 周期性会议 日期更新 回写 复制参会者
class db_writebacker(Thread):

	def __init__(self, sequence):
		super(db_writebacker, self).__init__()
		self.sequence = sequence

	def run(self):
		_plen = len(self.sequence)
		#dbrt = METTING.update_nextdtimes(self.sequence)
		for i in range(_plen):
			n = self.sequence.pop(0)
			loger.info("write meeting<%s> back to db." % n.name)
			if n.status2 == mnode.STA2_OVERP:
				# 超出周期，写入数据库并移除
				METTING.update(n.mid, status=METTING.STA_OVERP)
				continue
			elif n.status2 == mnode.STA2_TODAY_DONE:
				METTING.update(n.mid, status=METTING.STA_FINISH)
				n.db_done()
				continue
			else:
				#n.status == mnode.STA_UPDATED:
				loger.info(f"update next for meeting: {n.name}, on counting: {n.counting}")
				METTING.update_nextdtime(n.mid, n.nextdtime, n.counting)
				ATTENDERS.copy_attenders(n.mid, n.counting)
				if n.mroom:
					MROOM.set_next_auto(n.mroom, n.mid, n.nextdtime)
				n.set_updated()
			# Qer._con_pool.execute_db('update {meeting_tbl} set nextdtime="{nextdtime}" where mid={mid};update {mroom_tbl} set next_meeting={mid},next_mdtime="{nextdtime}" where roomid={roomid} and next_mdtime>"{nextdtime}"')

class m_announcer(Thread):
	def __init__(self, sequence):
		super(m_announcer, self).__init__()
		self.sequence = sequence

	def run(self):
		_plen = len(self.sequence)
		for i in range(_plen):
			n = self.sequence.pop(0)
			roomname = MROOM._vget(n.mroom, 'name') or ""
			wxusers = ATTENDERS.wx_attender(n.mid, n.counting) # couting for repeateds
			if not wxusers:
				loger.warning("无用户参会！%s" % n.name)
				n.set_announced()
				continue
			loger.info('m_announcer: %s' % wxusers)
			#school = myschool.myschool(n.objid)
			school = app_school(n.objid)
			msger = pmsgr(school)
			msger.text("开会:\n%s\t%s\t%s" % (n.name, n.nextdtime, roomname))
			msger.send2user(wxusers)
			n.set_announced()
