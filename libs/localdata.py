#!/usr/bin/env python
# -*- coding: utf8
import os
try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle


# 本地化存储，序列文件存储
class local_storage(object):
    def_workdir = "localdata"

    def __init__(self, workpath=None):
        if workpath is None:
            workpath = os.path.join(os.getcwd(), self.__class__.def_workdir)
        if not os.path.exists(workpath):
            os.mkdir(workpath)
        self.workpath = workpath

    def load_data(self, filename):
        raise NotImplementedError

    def save_data(self, filename):
        raise NotImplementedError


# 本地化txt存储
class txtfile(local_storage):

    def load_data(self, filename):
        pass

    def save_data(self, filename):
        pass

    def _deserialization(self, data_str):
        pass


# 本地化py存储
class pyfile(local_storage):

    pass


# 本地化cPickle存储
class binfile(local_storage):

    @classmethod
    def fromfile(cls, filename):
        # filename could be fullpathwithname
        if os.path.exists(filename):
            # fullpathname
            path,file = os.path.split(filename)
            t = cls(path)
        else:
            t = cls()
            file = filename
        return t.load_data(file)
    
    def load_data(self, filename, chart=None):
        tf = os.path.join(self.workpath, filename)
        if not os.path.exists(tf):
            print(ValueError("%s Not Exists!" % filename))
            return None
        with open(tf, 'rb') as dumpfile:
            data = pickle.load(dumpfile)
        return data

    def save_data(self, data_obj, filename):
        tf = os.path.join(self.workpath, filename)
        if not os.path.exists(tf):
            print('not exists and create!')
        with open(tf, 'wb') as dumpfile:
            pickle.dump(data_obj, dumpfile)
        return True