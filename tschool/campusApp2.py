#!/usr/bin/env python
# -*- coding: utf8
# 
import logging
import time
import os
import copy
from hashlib import md5
loger = logging.getLogger()

#logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-10s) %(message)s')

"""
fulltoken = {
    'devCode': 'aAyJUKMeTNvJwM2D',
    'devType': 2,
    'objectid': 'FbjunepfvxmasyRT4done', #华拓
    #'objectid': 'EzQ319HuHN8done', #sandbox school
    'objType': 2,
    'key': '8960773cce4357511f6a93cb43e1bb01',
    'keyId': '',
    'openAppID': '992684154779',
    'AppSecret': '9ca0f2afb72df10e6abf76ac5ab96076',
    'H5Secret': 'd505b237ac20aadb07313e47491dfa13'
}
"""

class extserver(object):
    WORKDIR = ''
    system_mode = 1
    token = {}
    svr_key = ''

    def signer(self, key, timestamp=0, gets=1, reqs=None, others=None):
        #reqs a dict data with token
        #check in https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=20_1 OK
        #reqs and others both to sign
        #others not in url(post data)
        #gets: 0: only sign-md5; 1: url_with_sign; 2: url_with_sign,md5(tuple)
        workd = dict()
        workd.update(self.token) # class token
        workd['timestamp'] = timestamp or int(time.time())
        curkey = ''
        cpos = 0
        reqs = reqs or {}

        def seperate(curkey, cpos, ind):
            # flat the reqd into workd
            for k,v in ind.items():
                if isinstance(v, dict):
                    cpos += 1
                    curkey += '[%s]' % k if cpos > 1 else k
                    seperate(curkey, cpos, v)
                else:
                    if cpos > 0:
                        workd[curkey + '[%s]' % k] = v
                    else:
                        workd[k] = v
            cpos -= 1
            curkey = curkey[:curkey.rindex('[')] if cpos > 1 else curkey

        seperate(curkey, cpos, reqs)
        ostr = '&'.join(['%s=%s' % (k, workd[k]) for k in sorted(workd)])

        #print ostr
        if others:
            # for post that not in url
            calstr = ""
            seperate("", 0, others)
            calstr = '&'.join(['%s=%s' % (k, workd[k]) for k in sorted(workd)])
            #print calstr
            #calstr = calstr.decode('gbk').encode('utf8')
            calstr += '&key=%s' % key
            #calstr = calstr.encode('utf8') if isinstance(calstr, unicode) else calstr.decode('gbk').encode('utf8')
            calstr = calstr.encode('utf8')
            print(calstr)
            # or gbk?
            md5out = md5(calstr).hexdigest().upper()
        else:
            otmp = ostr + '&key=%s' % key
            #otmp = otmp.encode('utf8') if isinstance(otmp, unicode) else otmp.decode('gbk').encode('utf8')
            otmp = otmp.encode('utf8')
            md5out = md5(otmp).hexdigest().upper()
        #print md5out
        if gets == 1:
            ostr += '&sign=%s' % md5out
            return ostr
        elif gets == 0:
            return md5out
        else:
            ostr += '&sign=%s' % md5out
            return md5out,ostr

# 学校自己开发
class selfserver(extserver):

    system_mode = 1
    token = {
        #   tokenid: appid; tokense: secret
        'devCode': '',  # 开发者标识。获取方式：学校/上级单位后台==》学校管理/基本信息==》开发者标识（仅学校创建者可见）
        'devType': 1,   # 开发者类型（1：上级单位，2：学校）
        'objectid': '', #学校/上级单位ID。
        'objType': '',  # object类型（1：上级单位，2：学校）
    }
    svr_key = ''

    def handle_msger(self, reqs=None, others=None):
        return self.signer(self.svr_key, reqs=reqs, others=others)


# 学校授权开发
class assist_svr(extserver):

    system_mode = 2
    token = {
        #   tokenid: appid; tokense: secret
        'devCode': '',  # 开发者标识。获取方式：学校/上级单位后台==》学校管理/基本信息==》开发者标识（仅学校创建者可见）
        'devType': 5,   # 开发者类型（1：上级单位，2：学校）
        'objectid': '', # 学校/上级单位ID。
        'objType': 2,  # object类型（1：上级单位，2：学校）
        'keyId': '', # 授权密钥标号
    }
    svr_key = '' # 授权密钥

    def __init__(self):
        if 'key' in self.token:
            self.svr_key = self.token.pop('key')
        else:
            self.svr_key = self.__class__.svr_key
        print(self.token, self.svr_key)

    def handle_msger(self, reqs=None, others=None):
        return self.signer(self.svr_key, reqs=reqs, others=others)


# 第三方开发
class thirdsvr(extserver):

    system_mode = 3
    token = {
        'openAppID': '',
        'objectid': '',
        'objType': '',
        'keyId': '', # 授权密钥标号
    }
    svr_key = '' # 授权密钥//或者AppSecret

    def handle_msger(self, reqs=None, others=None):
        return self.signer(self.svr_key, reqs=reqs, others=others)


class thirdsvr2(extserver):
    # 该方式不支持调用写入接口。
    # 该方式不支持获取高级字段（需要安全校验的字段）
    # https://open.campus.qq.com/doc/?item_id=3&page_id=175 使用应用（openAppID）方式
    # user_no // cellphone 为安全校验字段，在第三方独立应用中不能获取！
    system_mode = 5
    token = {
        'devType': 5,
        'openAppID': '',
        'AppSecret': '',
        'objectid': '',
        'objType': 2,
        #'keyId': '', # 授权密钥标号
    }
    svr_key = '' # 授权密钥//或者AppSecret

    @classmethod
    def gen_token(cls, token_data):
        token = {}
        for k in thirdsvr2.token:
            token[k] = token_data[k]
        return token

    def __init__(self):
        if 'AppSecret' in self.token:
            self.svr_key = self.token.pop('AppSecret')
        else:
            self.svr_key = self.__class__.svr_key
        print(self.token, self.svr_key)

    def handle_msger(self, reqs=None, others=None):
        return self.signer(self.svr_key, reqs=reqs, others=others)