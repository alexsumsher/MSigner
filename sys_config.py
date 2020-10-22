#!/usr/bin/env python
# -*- coding: utf8
# 
import base_config
import os
import logging
import json

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, (str, int, float)):
            return str(obj)
        else:
            return json.JSONEncoder.default(self,obj)

logging.basicConfig(level=logging.DEBUG, filename='nyscore_server.log', filemode='w', format='(%(funcName)-10s) %(message)s')
loger = logging.getLogger()

cur_config = base_config.config()
# 数据库配置
cur_config.addconf('dbserver', {
        'host': 'localhost',
        'port': 3306,
        'user': 'signerA',
        'password': 'htch-db1x',
        'db': 'msigner',
        'charset': 'utf8mb4',
        'connection_timeout': 5,
        'autocommit': True
    })
cur_config.addconf('testdb', {'host': '139.9.218.122','port': 3306,'user': 'signerA','password': 'htch-db1x', 'autocommit': True, 'db': 'msigner','charset': 'utf8mb4','connection_timeout': 5})
cur_config.addconf("meeting", {
    "PRE_ANNOUNCE_TIME": 30
    })

class fconfig(object):
    #flask config
    mode = 'development'
    #mode = "product"

cur_config.fconf = fconfig
#cur_config.conf_server('mode', 'development')

# system
cur_config.system('cache_size', 128)
cur_config.system('cache_keeptime', 3600)
cur_config.system('mysql_cons', 5)
cur_config.system("syscode", "hitouch-msigner")
cur_config.system("qqcrt", "project/qq_campus.crt")

# others
cur_config.cnf_set('default_objid', "no_obj_id") # default objid as test)

# 路径配置
cur_config.folder('base_fd', os.getcwd())
cur_config.folder('data_fd', 'localdatas')
cur_config.folder('static_fd', 'statics')
cur_config.folder('tmp_fd', 'tmp')
cur_config.folder('templates', 'xlsx_tpl')
cur_config.folder('uploads', 'uploads')

"""
cur_config.update({
    'objectid': '2XaxJgvRj6Udone',
    'objType': 2,
    'devCode': 'NpIWLrJYKbW7gmI8',
    'devType': 2,
    'key': '3d52bad98d5fe86d324bdc4b967eae23', # 南油developkey
    'keyId': '',
    'openAppID': '567087157207',
    'AppSecret': '923fe57239cb37da6820ea3451a498d6',
    'H5Secret': 'd505b237ac20aadb07313e47491dfa13'
    })
"""
cur_config.addconf('app_token', {
    #'objectid': '2XaxJgvRj6Udone', #华拓
    'objectid': '', # SAND SCHOOL
    'objType': 2,
    'devCode': 'TSZPNQS7XFlvMyrA',
    'devType': 5,
    #'key': 'f4ca55a1bd0a0f113bb18b573ee308aa', # 开发者
    #'keyId': '',
    'openAppID': '975365158436',
    'AppSecret': 'c13f6f449ae9f860211fdca22ec8663a',
    'H5Secret': 'd505b237ac20aadb07313e47491dfa13'
    })
cur_config.addconf('school_token', {
    'objectid': '', # SAND SCHOOL
    'objType': 2,
    'devCode': 'TSZPNQS7XFlvMyrA',
    'devType': 5,
    'key': 'dd451d390fda34d77b666ce935af7acf', # 开发者
    'keyId': 3117,
    })
    #'openAppID': '975365158436',
    #'AppSecret': 'c13f6f449ae9f860211fdca22ec8663a',
    #'H5Secret': 'd505b237ac20aadb07313e47491dfa13'

"""cur_config.update({
    'Action': '', # 接口名
    'SecretId': 0, #应用ID
    'OrgId': 0, #机构id
    'Nonce': 11886, #随机正整数
    'SecretKey ': ''
    })
"""