#!/usr/bin/env python
# -*- coding: utf8

from libs import binfile
import os
import time


# 该类应该比较适合用于中继服务器
# 将数据有限时间内的本地化
# 未做size限制
# 
keepings = {}
# on this server: we will keep some cachers for mapping
# 
def add(c):
    if c.name in keepings:
        raise ValueError("Exists!")
    keepings[c.name] = c

def remove(name):
    try:
        keepings.pop(name)
    except KeyError:
        return None
    return True

def get(name):
    return keepings.get(name)


class timedcacher(dict):
    work_dir = os.getcwd()
    keeptime = 86400 # 1day

    @classmethod
    def fromfile(cls, filename, loader=None):
        f = binfile(cls.work_dir)
        data = f.load_data(filename)
        info = data.pop('__info__')
        t = cls(data)
        t.ini(info['name'], info['keeptime'], info['lastime'])
        return t

    def ini(self, name, keeptime, lastime, loader, atonce, args=(), **kwargs):
        self.name = name
        self.keeptime = keeptime or self.__class__.keeptime
        self.lastime = lastime
        self.loader2 = None
        if loader:
            return self.setloader(loader, atonce, *args, **kwargs)
        else:
            self.loader = None

    def setloader(self, loader, atonce, *args, **kwargs):
        if callable(loader):
            self.loader = loader
            if args:
                self.args = args
            if kwargs:
                self.kwargs = kwargs
            if atonce:
                return self._load()
        else:
            self.loader = None

    def _load(self, *args, **kwargs):
        if not self.loader:
            return None
        args = args or self.args if hasattr(self, 'args') else []
        kwargs = kwargs or self.kwargs if hasattr(self, 'kwargs') else {}
        datas = self.loader(*args, **kwargs)
        if datas and isinstance(datas, dict):
            self.update(datas)
            self.save()
            self.lastime = time.time()
            return self
        else:
            raise RuntimeError("can not load data.")

    def setloader2(self, loader2, argfrom, argkeys):
        # dynamic args
        # 适用于动态预制参数
        if not callable(loader2):
            raise ValueError("loader2 must be a callable")
        for key in argkeys:
            if not hasattr(argfrom, key):
                raise ValueError("key: %s not in container: %s" % (key, str(argfrom)))
        self.argfrom = argfrom
        self.argkeys = argkeys
        self.loader2 = loader2

    def _load2(self):
        args = []
        for arg in self.argkeys:
            if hasattr(self.argfrom, arg):
                args.append(getattr(self.argfrom, arg))
        try:
            datas = self.loader2(*args)
        except:
            return None
        if datas and isinstance(datas, dict):
            self.update(datas)
            self.save()
            self.lastime = time.time()
            return self
        else:
            raise RuntimeError("can not load data.")

    def save(self, binfilepath=None):
        binfilepath = binfilepath or self.__class__.work_dir or os.getcwd()
        saver = binfile(binfilepath)
        tdata = dict()
        tdata.update(self)
        tdata['__info__'] = {'name': self.name, 'loader': str(self.loader), 'keeptime': self.keeptime, 'lastime': self.lastime}
        saver.save_data(tdata, os.path.join(binfilepath, self.name))

    def getdata(self, *args, **kwargs):
        now = time.time()
        if now - self.lastime < self.keeptime:
            return self
        try:
            return self._load2() if self.loader2 else self._load(*args, **kwargs)
        except RuntimeError:
            return None
