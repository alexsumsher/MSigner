#!/usr/bin/env python
# -*- coding: utf8

import requests


env = {
	#'appid': 'wxffe0dfeadc254daf',
	#'secret': 'b1733d34a316869eef74c54517c8b536',
	'appid': 'wx7af5e4cc74980097',
	'secret': 'c1d9170380f2c10300907b018c4ff30e',
	#'appid': 'wx3d2a21da95b17a25',
	#'secret': '9c626d312276a5ebc9ac9ccb998fa72d',
	'baseurl': 'https://api.weixin.qq.com/sns/',
	'code2Session': 'jscode2session',
}


def _takeurl(partname):
	if partname in env:
		return env['baseurl'] + env[partname]
	raise ValueError("unknown partname(%s)" % partname)

def wx_logon(js_code):
	url = _takeurl('code2Session')
	r = requests.get(url, params={'appid': env['appid'], 'secret': env['secret'], 'js_code': js_code, 'grant_type': 'authorization_code'})
	print(r.text)
	try:
		jrt = r.json()
	except:
		return
	print(jrt)
	# {"session_key":"T6Y4kxwO+orwCzocHb7hSA==","openid":"oXg0L40TMtx9JRRkrAVQU0GLeRMk"}
	return jrt

