#!/usr/bin/env python
# -*- coding: utf8

"""
OA: 会议签到系统
基于ibeacon(plus wifi) + 小程序 on 智慧校园
thirdsvr (server mode = 3)的方式开发。
PYTHON 3, NGINX, MYSQL
"""
import os
import time
import sys
import logging
import signal
from datetime import datetime
from flask import Flask, request, send_from_directory, send_file, redirect, url_for, session, abort, json
from werkzeug.utils import secure_filename
from ultilities import check_client

from libs import com_con,Qer
from tschool import myschool
import wxmnp
from cur_config import cur_config, logging
from modules import Mqueue
from modules import meeting

#logging.basicConfig(level=logging.DEBUG, filename='sm_server.log', filemode='w', format='(%(funcName)-10s) %(message)s')
loger = logging.getLogger()
loger.debug("starting server now...")
# 初始化db连接池
com_cons = com_con('test', cur_config.testdb, length=3, debug=True)
Qer.set_con_pool(com_cons)
# 初始化管理队列
Mqueue.set_announcer(None)
Mqueue.set_dbwritebacker(None)
Mqueue.set_synctime()
# 从数据库加载会议队列到内存
for m in meeting.load_all_meetings(datetime.today()):
	print(m)
	keys = meeting.key_list
	_mid = m[0]
	_objid = m[1]
	_name = m[2]
	_ondate = m[8]
	_ontime = m[9]
	_mtime = m[10]
	_rpmode = m[12]
	_rparg = m[13]
	node = mnode(_mid, _name, rpmode=_rpmode, rparg=_rparg, ondate=_ondate, ontime=_ontime, holdtime=_mtime)
	Mqueue.auto_node(node, _objid)
# 初始化Flask
app = Flask(__name__)
#app.config.from_object(cur_config.fconf)
app.secret_key  = os.environ.get('SECRET_KEY') or 'zxf***YFJEU7#@#1HFEiefj'
app.env = cur_config.conf_server('mode')

#紧急：fake server[临时]
class muser(object):
	store = {}

	@classmethod
	def get(cls, openid, **kwargs):
		if openid in cls.store:
			return cls.store[openid]
		elif 'js_code' in kwargs and 'session_key' in kwargs:
			return cls(openid, kwargs['js_code'], kwargs['session_key'])

	def __init__(self, openid, js_code, session_key, loadtime=0, unionid=None):
		self.js_code = js_code
		self.openid = openid
		self.session_key = session_key
		if self.loadtime == 0:
			self.loadtime = time.time()
		else:
			self.loadtime = loadtime
		if openid not in self.__class__.store:
			self.__class__.store[openid] = self

def signal_shutdown(sig, frame):
	Mqueue.stop_syc()
	print('over')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_shutdown)



@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	if request.method == 'GET':
		if 'action' not in request.args:
			'go for page html'
			# check client
			ua = request.headers.get('User-Agent')
			print(ua)
			client = check_client(ua)
			if client == 'mobile':
				return send_file('statics/htmls/mgm_mobile.html', mimetype='text/html')
			elif client == 'wx':
				return 'wx index page'
			else:
				return 'pc index page'
		openid = session.get("openid")
		if openid:
			user = muser.get(openid)
			rtdata['msg'] = 'logoned-index'
			rtdata['data'] = user.loadtime
		else:
			rtdata['success'] = 'no'
		return json.dumps(rtdata)
	print(request.form)
	return json.dumps(rtdata)

@app.route("/api/<target>", methods=['GET', 'POST'])
def API(target):
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	action = request.args.get('action')
	if request.method == 'GET':
		return json.dumps(rtdata)
	# ON POST
	if target == 'meeting':
		if action == 'new':
			print(request.form)
	return json.dumps(rtdata)

@app.route("/regs", methods=['GET'])
def onreg():
	rtdata = {'success': 'yes', 'msg': 'done', 'code': 0, 'data': None, 'dlen': 0}
	print(request.args)
	js_code = request.args.get("js_code")
	if js_code:
		wx_rsp = wxmnp.wx_logon(js_code)
		if wx_rsp['errcode'] == 0:
			#成功
			user = muser(wx_rsp['openid'], js_code, wx_rsp['session_key'])
			session['openid'] = wx_rsp['openid']
			rtdata['openid'] = wx_rsp['openid']
			rtdata['userid'] = len(muser.store) + 1
			return json.dumps(rtdata)
	rtdata['success'] = 'no'
	return json.dumps(rtdata)

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


@app.route('/resource/<filen>', methods=['GET'])
def resource(filen=''):
	return redirect(url_for('statics'))
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


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=7890)