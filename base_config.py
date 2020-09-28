#!/usr/bin/env python
# -*- coding: utf8
#
import os

class config(object):
    
    def __init__(self, **kwargs):
        # defaults
        self.data = {
            'devCode': '',
            'devType': 5, # 开发者类型（3：合作伙伴，5：开发者）
            'objectid': 'FbjunepfvxmasyRT4done', #华拓
            'keyId': '',
            'objectid': '', #sandbox school
            'objType': 2,
            'key': '', #&key=AppSecret
            'openAppID': '',
            'AppSecret': '9ca0f2afb72df10e6abf76ac5ab96076',
            'H5Secret': 'd505b237ac20aadb07313e47491dfa13'
        }
        self.server = {
            'port': 7890,
            'mode': 'development'
        }
        self._system = {

        }
        self.others = {}
        self.folders = {}
        self.folders['base_fd'] = os.getcwd()
        # setings
        for k,v in kwargs.items():
            if k in self.data and v:
                self.data[k] = v
                continue
            if k in self.server and v:
                self.server[k] = v
                continue
            self.others[k] = v

    def __getitem__(self, im):
        return self.data.get(im) or self.server.get(im) or self.others[im]

    def __setitem__(self, im, iv):
        if im in self.data:
            self.data[im] = iv
        elif im in self.server:
            self.server[im] = iv
        else:
            self.others[im] = iv

    def cnf_get(self, key, part=None):
        part = part or 'others'
        try:
            return getattr(self, part)[key]
        except:
            return None

    def cnf_set(self, key, value, part=None):
        part = part or 'others'
        try:
            getattr(self, part)[key] = value
        except:
            return None
        return value

    def update(self, datas, target=None):
        if target and target in ('data', 'server', '_system', 'others'):
            _t = getattr(self, target)
        else:
            _t = self.data
        for k,v in datas.items():
            if k in _t and v:
                _t[k] = v

    def token(self):
        return self.data

    def conf_server(self, name, value=None):
        if isinstance(name, dict):
            self.server.update(name)
            return
        if value:
            self.server[name] = value
        else:
            return self.server[name]

    def system(self, name, value=None):
        if isinstance(name, dict):
            self._system.update(name)
            return
        if value:
            self._system[name] = value
        else:
            return self._system[name]

    def folder(self, fdname, pathname='', basefd=''):
        if not pathname:
            return self.folders.get(fdname)
        if fdname == 'base_fd' and os.path.isdir(pathname):
            self.folders['base_fd'] = pathname
        basefd = basefd or self.folders.get('base_fd') or os.getcwd()
        fdpath = os.path.join(basefd, pathname)
        if os.path.isdir(fdpath):
            self.folders[fdname] = fdpath
            return fdpath

    def conf_others(self, name, value=None):
        if isinstance(name, dict):
            self.others.update(name)
            return
        if value:
            self.others[name] = value
        else:
            return self.others[name]

    def addconf(self, name, conf):
        if not hasattr(self, name):
            setattr(self, name, conf)

    # import config data from dynamic file
    def ext_from_py(self, pyfile, conf_type="data"):
        if not hasattr(self, conf_type):
            logging.error('error: no a type name: %s in config' % conf_type)
            return None
        context = getattr(self, conf_type)
        try:
            f = open(pyfile, 'r')
            exec(f.read(), globals(), context)
        except:
            logging.error("not correct import data.")
            return None
        return str(context)

    def load_dyconf(self, folder_path):
        # from a folder import all dynamic config data for updating/modify
        for f in os.listdir(folder_path):
            n = os.path.splitext(f)[0]
            self.ext_from_py(os.path.join(folder_path, f), n)