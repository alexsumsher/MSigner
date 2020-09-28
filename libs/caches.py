#!/usr/bin/env python
# -*- coding: utf8
# 
import time
from threading import Timer, Lock

class time_cacher(dict):
    # time cacher + gard functions
    cache_list = []
    otherjobs = None
    otherjob_target = None
    stimer_flag = True
    ins_limit = 8
    ctime_max = 300
    ctime_min = 10
    keep = 180
    time_checker = None

    @classmethod
    def set_checker(cls, checktime=60, autostart=True):
        if checktime < cls.ctime_min:
            logging.warning("interval_slot less then 30, and fix to 30.")
            checktime = cls.ctime_min
        elif checktime > cls.ctime_max:
            logging.warning("interval_slot over ctime_max, please care.")
            checktime = cls.ctime_max
        cls.interval_slot = checktime
        if autostart:
            cls.check_timer()

    @classmethod
    def check_timer(cls):
        if cls.stimer_flag is False:
            print("stop")
            cls.stimer.cancel()
            return
        if len(cls.cache_list) > cls.ins_limit:
            logging.warning("lsourcer instance too many (over %s)!" % cls.ins_limit)
        print("stating sync...")
        _ctime = time.time()
        for i in cls.cache_list:
            i._clear(_ctime)
        cls.stimer = Timer(cls.interval_slot, cls.check_timer)
        cls.stimer.start()
        #print("starting timer for sync... with interval %s" % cls.interval_slot)
    
    @classmethod
    def bind_checker(cls, time_checker, autostart=True):
        # time_checker: 外部定时器
        # time_checker.start/stop/check
        if cls.stimer:
            raise RuntimeError("stimer mode!")
        if callable(time_checker) and hasattr(time_checker, 'stop'):
            cls.time_checker = time_checker
        else:
            raise TypeError("Wrong type")
        if autostart and hasattr(time_checker, 'start'):
            cls.time_checker.start()

    @classmethod
    def stop_checker(cls, clear=False):
        if cls.stimer and cls.stimer.is_alive():
            cls.stimer.cancel()
            cls.stimer = None
        elif cls.time_checker:
            try:
                cls.time_checker.stop()
            except AttributeError:
                pass
        if clear:
            cls._clear()

    @classmethod
    def _clear(cls):
        for i in cls.cache_list:
            i._clear(0, force=True)
        cls.cache_list.clear()

    def __init__(self, size=32, keep=0):
        if self.__class__.ins_limit <= len(self.__class__.cache_list):
            raise RuntimeError("time cacher over instance!")
        self.keep = keep or self.__class__.keep
        self.count = 0
        self.size = size
        self.__class__.cache_list.append(self)

    def _clear(self, checktime, force=False):
        if force:
            for v in self.values():
                v.clear()
            self.clear()
            return
        for v in self.values():
            if checktime - v['_T'] > self.keep:
                v['_V'] = None
                v['_T'] = 0
                self.count -= 1

    def set(self, key, value):
        if key in self:
            self[key]['_T'] = time.time()
            self[key]['_V'] = value
            return value
        elif self.count > self.size:
            #raise RuntimeError("Over size!")
            return False
        else:
            self[key] = {'_T': time.time(), '_V': value}
            self.count += 1
            return value

    def get(self, key):
        try:
            V = self[key]
        except KeyError:
            return None
        return V['_V']


class LRU2Q(object):
    fifo_len = 20
    lru_len = 20

    @classmethod
    def cset_flen(cls, length):
        if length > 10:
            cls.fifo_len = length

    @classmethod
    def cset_llen(cls, length):
        if length > 10:
            cls.lru_len = length

    def __init__(self, key, flen=0, llen=0):
        self.flen = flen or self.__class__.fifo_len
        self.llen = llen or self.__class__.lru_len
        self.fq = []
        self.lq = []
        self.key = key

    def __getitem__(self, idx_or_keyvalue):
        #   get item by key or keyvalue
        if isinstance(idx_or_keyvalue, int):
            try:
                to = self.fq[idx_or_keyvalue]
            except IndexError:
                try:
                    to = self.lq[idx_or_keyvalue]
                except IndexError:
                    pass
                self._2top(idx_or_keyvalue)
                return to
            self._fq2lq(idx_or_keyvalue)
            return to
        idx,to = self._checkitem(self.fq, idx_or_keyvalue)
        if to:
            self._fq2lq(idx)
            return to
        else:
            idx,to = self._checkitem(self.lq, idx_or_keyvalue)
            if to:
                self._2top(idx)
                return to
            else:
                #   not in queue, push
                return None

    def push(self, item):
        #   push a new item to fifo queue, must in fifo
        v = item.get(self.key) if isinstance(item, dict) else item.__dict__.get(self.key)
        if not v:
            raise ValueError('item to push withou a key name: %s' % self.key)
        delta_len = len(self.fq) - self.flen + 1
        #   cause a new one to add, if cur len == max len, also kick
        if delta_len > 0:
            for i in range(delta_len):
                self.fq.pop(0)
        if self[v]:
            return self[v]
        else:
            self.fq.append(item)
        return item

    def _checkitem(self, arr, match):
        i = 0
        key = self.key
        if isinstance(arr[0], dict):
            for item in arr:
                if item[key] == match:
                    return i,item
                i += 1
        else:
            for item in arr:
                if item.__dict__[key] == match:
                    return i,item
                i += 1
        return -1,None

    def _2top(self, idx):
        if idx == 0:
            return idx
        elif idx > 0:
            try:
                to = self.lq.pop(idx)
            except IndexError:
                return -1
            self.lq.insert(0, to)
            return idx

    def _fq2lq(self, fq_idx):
        try:
            to = self.fq.pop(fq_idx)
        except IndexError:
            return -1
        delta_len = len(self.lq) - self.llen + 1
        #   cause a new one to add, if cur len == max len, also kick
        if delta_len > 0:
            for i in range(delta_len):
                self.lq.pop()
        self.lq.append(to)
        return len(self.lq) - 1


class short_cache(object):
    limit_len = 30
    dead_len = 40

    def __init__(self, keyname, deadflag='', limit_len=0, dead_len=0):
        self.keyname = keyname
        self.limit_len = limit_len or self.__class__.limit_len
        self.dead_len = dead_len or self.__class__.dead_len
        if self.dead_len <= self.limit_len or self.limit_len < 6:
            raise RuntimeError("NOT leggal limit_len or dead_len!")
        self.store = {}
        self.clen = 0
        self.deadflag = deadflag
        self.ilock = Lock()

    def add(self, item):
        try:
            kn = item.__dict__.get(self.keyname) or item[self.keyname]
        except AttributeError:
            raise ValueError('NOT correct item!')
        if kn:
            if kn in self.store:
                setattr(item, 'ct', int(time.time()))
            else:
                if self.clen > self.limit_len:
                    self.ilock.acquire()
                    self.limit_len += self.__check()
                    self.ilock.release()
                setattr(item, 'ct', int(time.time()))
                self.store[kn] = item
                self.clen += 1
            return item
        else:
            raise ValueError('NOT correct item!')

    def __getitem__(self, key):
        item = self.store.get(key) or self.store.get(str(key))
        if item:
            item.ct = int(time.time())
        return item

    def exists(self, key):
        return key in self.store

    def leave(self, key):
        self.__clear(keyid=key)

    def __check(self):
        if self.limit_len >= self.__class__.dead_len:
            self.__clear(self.clen - self.__class__.limit_len)
            self.limit_len = self.__class__.limit_len
            self.clen = len(self.store)
            return 0
        else:
            return 1

    def __clear(self, num=0, keyid=''):
        if num > 0:
            c = num
            for k,v in sorted(self.store.items(), key=lambda x: x[1].ct):
                self.store.pop(k)
                c -= 1
                if c == 0:
                    return num
        if keyid and keyid in self.store:
            self.store.pop(keyid)
            return keyid
