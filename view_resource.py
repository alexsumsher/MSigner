import os
import json
from flask import request, session, abort

from tschool import myschool, pmsgr
from sys_config import cur_config, loger, DateEncoder
from modules import meeting as MEETING, attenders as ATTENDERS, mroom as MROOM, user_tbl as USER
from actions import mgr_actions, user_actions, data_handler


def RESOURCE(target=""):
	# 在智慧校园系统中 session丢失
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	objid = request.args.get('objectid') or session.get("objectid") or "2XaxJgvRj6Udone"
	userid = request.args.get('userid') or session.get('userid')
	print(session)
	userid = userid or 'anonymouse'
	if not objid:
		rtdata['msg'] = 'no objectid'
		rtdata['success'] = 'no'
		return json.dumps(rtdata, cls=DateEncoder)
	action = request.args.get('action')
	if target == 'meeting':
		if action == 'list':
			page = int(request.args.get('page'))
			size = int(request.args.get('page_limit', 20))
			overtime = request.args.get('overtime') == 'yes'
			summary = request.args.get('summary') == 'yes'
			lastid = int(request.args.get('last_id', 0))
			if summary:
				count, datas = MEETING.list_by_objid(objid, lastmid=lastid, page=0, pagesize=size, simple=True, summary=True)
				rtdata['dlen'] = count
				rtdata['data'] = datas
			else:
				datas = MEETING.list_by_objid(objid, lastmid=0, page=lastid, pagesize=0, simple=True)
				rtdata['data'] = datas
		elif action == 'mlist':
			# list for manager
			page = int(request.args.get('page'))
			size = int(request.args.get('page_limit', 20))
			overtime = request.args.get('overtime') == 'yes'
			rpmode = int(request.args.get('rpmode', -1))
			p_start = request.args.get('p_start')
			p_end= request.args.get('p_end')
			holder = userid if request.args.get('holder') == 'yes' else None
			summary = request.args.get('summary') == 'yes' or page == 1
			lastid = int(request.args.get('last_id', 0))
			handler = mgr_actions(objid)
			rtdata['data'] = handler.list_meetings2(rpmode=rpmode, p_start=p_start, p_end=p_end, holder=holder, page=1, size=size, summary=summary, overtime=overtime)
			if summary:
				rtdata['dlen'] = handler.extdata
		elif action == 'mylist':
			userid = request.args['userid']
			ondate = request.args.get('ondate') #could be None
			user_hanlder = user_actions(objid)
			meetings = user_hanlder.user_meetings(userid, ondate)
			if meetings:
				rtdata['data'] = meetings
		elif action == 'full_detail':
			# full detail get by manager
			mid = int(request.args.get('mid', 0))
			if mid > 0:
				handler = mgr_actions(objid)
				rtdata['data'] = handler.fullmeeting(mid)
		else:
			rtdata['success'] = 'no'
	elif target == 'mroom':
		if action == 'list':
			page = int(request.args.get('page'))
			size = int(request.args.get('page_limit', 20))
			summary = request.args.get('summary') == 'yes'
			lastid = int(request.args.get('last_id', 0))
			if summary:
				count, datas = MROOM.list(objid, page, size, lastid=lastid, summary=True)
				rtdata['dlen'] = count
				rtdata['data'] = datas
			else:
				datas = MROOM.list(objid, page, size, lastid=lastid)
				rtdata['data'] = datas
		elif action == 'schedule':
			roomid = int(request.args.get('roomid'))
			handler = mgr_actions(objid)
			period_from = request.args.get("period_from")
			period_end = request.args.get('period_end') #None
			#rtdata['data'] = handler.room_schedule(roomid, ondate, ontime)
			rtdata['data'] = handler.room_schedule2(roomid, period_from=period_from, period_end=period_end)
		elif action == 'available':
			# room available for special request
			ondate = request.args.get('ondate')
			ontime = request.args.get('ontime')
			mtime = int(request.args.get('mtime', 120))
			sign_mode = int(request.args.get('sign_mode'))
			handler = mgr_actions(objid)
			rtdata['data'] = handler.available_rooms(ondate=ondate, ontime=ontime, mtime=mtime, by_sign_mode=sign_mode)
		elif action == 'info':
			roomid = request.args.get["roomid"]
			rtdata['data'] = MROOM.detail(roomid)
		else:
			rtdata['success'] = 'no'
	elif target == 'users':
		if action == 'list':
			page = int(request.args.get('page'))
			size = int(request.args.get('page_limit', 20))
			summary = request.args.get('summary') == 'yes' or page == 1
			lastid = int(request.args.get('last_id', 0))
			onlyreged = request.args.get("onlyreged") == 'yes'
			dpid = request.args.get("departid") # 'dpid1,dpid2,...'
			user_list = USER.list_users(objid, page=page, size=size, only_reged=onlyreged, by_dpid=dpid)
			if not user_list:
				rtdata['success'] = 'no'
			elif summary:
				count = USER.count_users(objid)
				rtdata['dlen'] = count
			rtdata['data'] = user_list
		elif action == 'userinfo':
			uinfo = USER.user_by_userid(userid)
			print(uinfo)
			if uinfo:
				rtdata['data'] = uinfo
			else:
				rtdata['success'] = 'no'
	elif target == 'attenders':
		if action == 'list':
			page = 1
			size = 100
			mid = int(request.args.get('mid', 0))
			mcount = int(request.args.get('mcount', -1))
			# mtimes === mcount; 0 is the first, -1 as not set
			handler = mgr_actions(objid)
			attdrs = handler.list_attenders(mid, mcount)
			#attdrs = ATTENDERS.get_attenders(mid, mtimes=mcount)
			if attdrs:
				rtdata['data'] = attdrs
			else:
				rtdata['data'] = None
				rtdata['success'] = 'no'
	elif target == 'school':
		if action == 'list':
			as_option = request.args.get("as_option") == 'yes'
			dh = data_handler()
			rt = dh.list_schools(as_opts=as_option)
			if rt:
				rtdata['data'] = rt
			else:
				rtdata['success'] = 'no'
	return json.dumps(rtdata, cls=DateEncoder)
