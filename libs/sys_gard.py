#!/usr/bin/env python
# -*- coding: utf8
from threading import Timer, Lock

class sysG(object):
    glock = Lock()

    stimer = None
    stimer_flag = True

    interval_slot = 60 # 60s one time==1min
    sync_count = 0
    ins_storage = []
    ins_limit = 10

    @classmethod
    def set_synctime(cls, synctime, autostart=True):
        synctime = int(synctime)
        if synctime < 30:
            logging.warning("interval_slot less then 30, and fix to 30.")
            synctime = 30
        elif synctime > 60 * 60 * 24:
            logging.warning("interval_slot over one day, please care.")
        cls.interval_slot = synctime
        if autostart:
            cls.sync_timer()

    @classmethod
    def sync_timer(cls):
        if cls.stimer_flag is False:
            print("stop")
            cls.stimer.cancel()
            return
        if len(cls.ins_storage) > cls.ins_limit:
            logging.warning("lsourcer instance too many (over %s)!" % cls.ins_limit)
        #print("stating sync...")
        for i in cls.ins_storage:
            i._synchronize()
        cls.sync_count += 1
        cls.stimer = Timer(cls.interval_slot, cls.sync_timer)
        cls.stimer.start()
        #print("starting timer for sync... with interval %s" % cls.interval_slot)

    @classmethod
    def stop_syc(cls):
        if cls.stimer and cls.stimer.is_alive():
            cls.stimer.cancel()

    @classmethod
    def getinst(cls, idx=0):
        return cls.ins_storage[idx]
