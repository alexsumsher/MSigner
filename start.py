import os
import sys
import logging
import signal
from datetime import datetime

from libs import com_con,Qer
from sys_config import cur_config, loger
from modules import mnode, Mqueue
from modules import meeting
from actions import db_writebacker, m_announcer

#logging.basicConfig(level=logging.DEBUG, filename='sm_server.log', filemode='w', format='(%(funcName)-10s) %(message)s')
#loger = logging.getLogger()
loger.debug("starting server now...")
# 初始化db连接池
if sys.platform.startswith('win'):
	com_cons = com_con('test', cur_config.testdb, length=4, debug=True)
else:
	com_cons = com_con('test', cur_config.dbserver, length=5, debug=True)
Qer.set_con_pool(com_cons)

# 初始化管理队列
Mqueue.set_announcer(m_announcer)
Mqueue.set_dbwritebacker(db_writebacker)
Mqueue.set_synctime()


# 处理手动关闭ctrl+c
def signal_shutdown(sig, frame):
	Mqueue.stop_syc()
	print('mqueue over')
	com_cons.shutdown()
	print("cons shutdown")
	loger.warning("Manual Shutdown.")
	sys.exit(0)

# 从数据库加载会议队列到内存
starton = datetime.today()
for m in meeting.load_all_meetings(starton):
	print(m)
	sta = m[-1]
	_rpmode = m[13]
	if sta == meeting.STA_OVERP or (sta == meeting.STA_FINISH and _rpmode == mnode.RMODE_ONCE):
		continue
	#('mid', 'objid', 'name', 'holder', 'mroom', 'roomname', 'sign_mode',  'counting', 'lastetime', 'ondate', 'ontime', 'mtime', 'nextdtime', 'rpmode', 'rparg', 'sign_pre', 'sign_limit', 'p_start', 'p_end', 'status')
	_mid = m[0]
	_objid = m[1]
	_name = m[2]
	_mroom = m[4]
	_counting = m[7]
	_ondate = str(m[9])
	# ??? return time by timedelta.... => str(timedelta) => time
	_ontime = str(m[10])
	_mtime = m[11]
	_ndtime = m[12]
	_rparg = m[14]
	_p_start = m[17]
	_p_end = m[18]
	if _rpmode == mnode.RMODE_ONCE:
		node = mnode(_mid, _name, mroom=_mroom, rpmode=_rpmode, rparg=_rparg, ondate=_ondate, ontime=_ontime, mtime=_mtime)
	else:
		# check the nextdtime(m[9]) meeting ondate?over?futrue?
		#if m[9].day <= starton.day and sta == meeting.STA_FINISH:
		#	_counting += 1
		node = mnode(_mid, _name, mroom=_mroom, rpmode=_rpmode, rparg=_rparg, counting=_counting, ondate=_ondate, ontime=_ontime, mtime=_mtime, p_start=_p_start, p_end=_p_end)
		if node.nextdtime > _ndtime:
			print(node.nextdtime, 'over', _ndtime)
			node.force_update()
	Mqueue.auto_node(_objid, node)
#print(Mqueue.ins_queues)

try:
	from main_0 import app
except Exception as e:
	print('error: ', e)
	signal_shutdown(None, None)

if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal_shutdown)
	app.run(host='0.0.0.0', port=7890)