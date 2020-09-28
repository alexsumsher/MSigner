#!/usr/bin/env python
# -*- coding: utf8
# 
import base_config
import os
import logging

logging.basicConfig(level=logging.DEBUG, filename='nyscore_server.log', filemode='w', format='(%(funcName)-10s) %(message)s')

cur_config = base_config.config()
# 数据库配置
cur_config.addconf('dbserver', {
        'host': 'localhost',
        'port': 3306,
        'user': 'examer',
        'password': 'exm@runner!',
        'db': 'exams',
        'charset': 'utf8',
        'connection_timeout': 5
    })
cur_config.addconf('testdb', {'host': '120.77.244.198','port': 3306,'user': 'examer','password': 'exm@runner!','db': 'exams','charset': 'utf8','connection_timeout': 5})

class fconfig(object):
    #flask config
    #mode = 'development'
    mode = "product"

cur_config.fconf = fconfig
cur_config.conf_server('mode', 'product')

# system
cur_config.system('cache_size', 128)
cur_config.system('cache_keeptime', 3600)
cur_config.system('mysql_cons', 5)

# 路径配置
cur_config.folder('base_fd', os.getcwd())
cur_config.folder('data_fd', 'localdatas')
cur_config.folder('static_fd', 'static')
cur_config.folder('tmp_fd', 'tmp')
cur_config.folder('templates', 'xlsx_tpl')
cur_config.folder('uploads', 'uploads')

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