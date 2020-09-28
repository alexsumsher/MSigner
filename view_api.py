import os
from datetime import datetime as DT
from flask import request, session, abort, json
from ultilities import json_flat_2_list


from tschool import myschool, pmsgr, app_school
from sys_config import cur_config, loger
from modules import meeting as MEETING, attenders as ATTENDERS, mroom as MROOM, user_tbl as USER
from actions import mgr_actions, user_actions, system

#/?objectid=2XaxJgvRj6Udone&objType=2&userid=2y7M3LPNb4odone&timestamp=1586688086&sign=BAC3CB4662B8F8F96794E92780D9E14E
def API(target):
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	objid = request.args.get('objectid', "2XaxJgvRj6Udone")
	userid = request.args.get('userid') or session.get('userid')
	#userid = session.get('userid')
	if not userid:
		loger.error("no userid from session!")
		rtdata['success'] = 'no'
		rtdata['msg'] = "未登录"
		return json.dumps(rtdata)
	action = request.args.get('action')
	if request.method == 'GET':
		if target == 'meeting':
			if action == 'mylist':
				userid = request.args['userid']
				ondate = request.args.get('ondate') #could be None
				user_hanlder = user_actions(objid)
				rt = user_hanlder.user_meetings(userid, ondate)
			elif action == 'sign_status':
				mid = int(request.args.get('mid'))
				mcount = int(request.args.get('mcount', 0))
				rt = ATTENDERS.sign_status(mid, userid, mcount)
			else:
				rt = None
		if rt:
			rtdata['data'] = rt
		else:
			rtdata['success'] = 'no'
		return json.dumps(rtdata)
	# ON POST
	params = request.form.to_dict()
	print(params)
	#action = params.pop('action')
	if not objid:
		rtdata['msg'] = 'no objid!'
		rtdata['success'] = 'no'
		return json.dumps(rtdata)
	rt = None
	handler = None
	if target == 'meeting':
		if action == 'new':
			roomid = int(params.get("mroom", 0))
			params['holder'] = userid
			handler = mgr_actions(objid)
			mid = handler.newmeeting_safe(params, getndtime=True)
			if mid <= 0:
				rt = False
			else:
				rt = {'mid': mid, 'nextdtime': handler.extdata}
		elif action == 'modify':
			# 是否已经结束，是否已经超时
			pass
		elif action == 'sign':
			# 签到
			mid = int(params['mid'])
			userid = params['userid']
			mtimes = int(params.get('mtimes', 0))
			mcount = int(params.get('mcount', -1))
			roomid = int(params.get("roomid", 0))
			identify_key = params['room_identifier']
			user_hanlder = user_actions(objid)
			rt = user_hanlder.meeting_signin(userid, mid, identify_key, roomid=roomid, mcount=mcount)
			rtdata['msg'] = user_hanlder.extdata
		elif action == 'ask_off':
			mcount = int(params.get('mcount', -1))
			remark = params.get("remark")
			userid = params['userid']
			mid = int(params['mid'])
			user_hanlder = user_actions(objid)
			rt = user_hanlder.meeting_off(userid, mid, mcount=mcount, remark=remark)
		elif action == 'delete':
			mid = int(params['mid'])
			mcount = int(params.get('mcount', 0))
			handler = mgr_actions(objid)
			rt = handler.drop_meeting(mid, mcount)
		elif action == 'mod_rparg':
			# only same rpmode could action
			pass
	elif target == 'mroom':
		if action == 'new':
			roomid = MROOM.new(objid, params)
			if roomid and roomid > 0:
				rt = roomid
			else:
				rt = False
		elif action == 'modify':
			rt = MROOM.update(params)
	elif target == 'users':
		if action == 'import':
			users = json_flat_2_list(request.form)['users']
			print(users)
			# may conflict
			rt = USER.import_multi(users, objid)
			if not rt:
				rtdata['msg'] = "有已经导入的教师"
		elif action == 'importall':
			handler = mgr_actions(objid)
			rt = handler.import_all()
	elif target == 'attenders':
		mid = int(params.pop('mid'))
		mcount = int(params.get('mcount', -1))
		if not mgr_actions.action_ontime(objid, mid, mcount=mcount):
			rtdata['success'] = 'no'
			rtdata['msg'] = '当前会议相关配置不可操作（请确认您操作是否过时会议）'
			return json.dumps(rtdata)
		# 注意区分： 对于重复模式会议，只能修改未开始会议的参会者，当前会议是已完成则不能修改：只有idle状态（before announce）才能修改
		if action == 'add':
			attdrs = json_flat_2_list(params)['attenders']
			print(attdrs)
			rt = ATTENDERS.set_attenders(mid, attdrs, mtimes=mcount)
		elif action == 'delete':
			aid = int(request.form['aid'])
			rt = ATTENDERS.kick(aid)
		elif action == 'role':
			aid = int(request.form['aid'])
			roleid = int(request.form['roleid'])
			if roleid == 0:
				rt = ATTENDERS.set_assistor(aid, unset=True)
			elif roleid == 1:
				rt = ATTENDERS.set_assistor(aid)
		elif action == 'clear':
			mid = int(request.args['mid'])
			rt = ATTENDERS.drop_bymeeting(mid, mtimes=mcount)
		elif action == 'unset_status':
			# 重置状态 == 0
			aid = int(request.form['aid'])
			handler = mgr_actions(objid)
			rt = handler.reset_status(aid)
	elif target == 'message':
		if action == 'send_user':
			wxuserid = request.form['wxuserid']
			content = request.form['content']
			msgtype = request.form.get("msgtype", 'text')
			#ischool = myschool.myschool(objid)
			ischool = app_school(objid)
			msger = pmsgr(ischool, msgtype, content)
			msger.send2user(wxuserid)
	else:
		loger.error("unknown comd!")
		rt = False
	# rt: return value, most of times is return from execute_db, which will return False if not success!
	if not rt:
		rtdata['success'] = 'no'
		if handler:
			rtdata['msg'] = handler.emsg
	elif not rtdata['data']:
		rtdata['data'] = rt
	return json.dumps(rtdata)