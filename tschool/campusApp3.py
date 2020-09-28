#!/usr/bin/env python
# -*- coding: utf8
# 
import logging
import time
import os
import hmac
from hashlib import sha1
from random import randint
loger = logging.getLogger()

#logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-10s) %(message)s')
# 适配智慧校园平台2.0版本

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
    token = {}
    SecretKey = ''

    def _nonce(self):
        return randint(1000, 999999)

    def _hash_mac(self, key, code):
        hmac_code = hmac.new(key.encode(), code.encode(), sha1)
        return hmac_code.hexdigest()

    def signer(self, action, prefix, timestamp=0, gets=1, reqs=None, others=None):
        # prefix: 'GEToapi.campus.qq.com/v2/user/?'
        workd = dict()
        workd.update(self.token) # class token
        workd['Timestamp'] = timestamp or int(time.time())
        workd['Action'] = action
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
            calstr = prefix
            seperate(calstr, 0, others)
            calstr = '&'.join(['%s=%s' % (k, workd[k]) for k in sorted(workd)])
            #print calstr
            #calstr = calstr.decode('gbk').encode('utf8')
            #calstr = calstr.encode('utf8') if isinstance(calstr, unicode) else calstr.decode('gbk').encode('utf8')
            #calstr = calstr.encode('utf8')
            print(calstr)
            # or gbk?
            sign_txt = hmac.new(self.SecretKey.encode(), calstr.encode(), sha1)
            #md5out = md5(calstr).hexdigest().upper()
        else:
            #otmp = otmp.encode('utf8') if isinstance(otmp, unicode) else otmp.decode('gbk').encode('utf8')
            otmp = otmp.encode('utf8')
            sign_txt = hmac.new(self.SecretKey.encode(), calstr.encode(), sha1)
            #md5out = md5(otmp).hexdigest().upper()
        #print md5out
        if gets == 1:
            ostr += '&sign=%s' % sign_txt
            return ostr
        elif gets == 0:
            return sign_txt
        else:
            ostr += '&sign=%s' % sign_txt
            return sign_txt,ostr

    def handle_msger(self, action, reqs=None, others=None):
        return self.signer(action, reqs=reqs, others=others)