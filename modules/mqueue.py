from datetime import datetime as DT, timedelta
import time
import calendar
from threading import Thread, Timer, Lock
import logging
#logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-10s) %(message)s')
loger = logging.getLogger()

"""
实时状态管理器；用于发布通知，更新周期性会议状态（次日更新）
"""

class mnode(object):

    """ 
    A node of meeting queue! scan nodelist for available meeting in some day
    source from db, convert to mnode
    params:
    rpmode: repeatmode, byweek, bymonth, onetime
    rpvals: repeat argument, list or int, as choosen/interval of days

    actions: mid->db->detail
    """
    def_announce = 30

    RMODE_ONCE = 0
    RMODE_WEEKLY = 1
    RMODE_MONTHLY = 2
    RMODES = (0,1,2)

    STA_USELESS = -1 # one time meeting and after meeting day
    STA_IDLE = 0 # after today, waits for next time meeting
    STA_ONDATE = 1 # meeting day but before announce time
    STA_ANNOUNCE = 2 # before meeting and after announce time
    STA_ANNOUNCED = 3 # announced
    STA_PROGRESSING = 4 # on meeting
    STA_DONE = 5 # over holding time, still on meeting day
    STA_UPDATED = 6 # a nextdtime is set, will be writeback to db
    STA_CLOSED = 7 # meeting is over manually, ready to delete from Mqueue
    STA_TEXT = ('未到会议日', '当日会议', '待通知', '已通知', '会议中', '已结束', '日期更新', '已关闭', '待移除')

    STA2_TODAY_DONE = 10
    STA2_OVERP = 100
    STA2_FORCE_UPDATE = 200

    AUTO_DONE = True
    MDAYS = (None, 31, None, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    # 待更新序列：
    # 异步/新进程 实现回写更新了nextdtime(_gonext)到指定接口（mysql的meeting表） 每日执行一次即可/或每次mqueue扫描后
    # 查看update_sequence是否为空，不为空则(异步)调用回写;
    # update_sequence: [node, node, ...]
    update_sequence = []
    last_writeback_day = 0 #最近一次完成回写后的日期数
    announce_sequence = []

    @classmethod
    def wb_day(cls, day=None):
        if isinstance(day, int) and 0<day<31:
            cls.last_writeback_day = day
        else:
            return cls.last_writeback_day

    @classmethod
    def clear_update_sequence(cls):
        loger.info("clear update_sequence with length: %s" % len(cls.update_sequence))
        cls.update_sequence.clear()

    @classmethod
    def clear_announce_sequence(cls):
        loger.info("clear announce_sequence with length: %s" % len(cls.announce_sequence))
        cls.announce_sequence.clear()

    @classmethod
    def set_def_announce(cls, n):
        if 5 < n < 120:
            cls.def_announce = n

    def __init__(self, mid, name, mroom=0, rpmode=0, rparg=1, counting=0, ondate=None, ontime=None, mtime=120, p_start=None, p_end=None):
        # nextdtime/nexttime meetting start d/time
        # ondate: string('YY-mm-dd'); ontime: string('HH:MM:SS')
        # announce, mtime: by minute
        # if mroom == 0: no room 
        # p_start/p_end: datetime with 0 of hour/minute/second/microsecond
        if not isinstance(mid, int) and mid>=0:
            raise ValueError("MID MUST GIVENT!")
        self.mid = mid # mid could be zero, for pre create, after inert to db, the mid will get
        self.name = name
        self.mroom = mroom
        self.rpmode = rpmode
        self.counting = counting
        self.mtime = mtime
        self.announce = self.__class__.def_announce
        self.status = self.__class__.STA_IDLE
        self.status2 = 0 # 增加辅助状态，用于其他作用；如更新为overp
        #self.ondate = DT.strptime(ondate, '%Y-%m-%d') if isinstance(ondate, str) else ondate
        #self.ontime = DT.strptime(ontime, '%H:%M:%S') if isinstance(ontime, str) else ontime
        if self.rpmode == self.__class__.RMODE_ONCE:
            today = DT.today()
            self.nextdtime = DT.strptime(ondate + ' ' + ontime, '%Y-%m-%d %H:%M:%S')
            if self.nextdtime < today:
                print("worong dt")
                raise ValueError("A new NODE of ONCE MEETING with overed time!")
            self.rparg = 1
            return
        # Part of repeatly meetings
        # check period
        self.p_start = DT.strptime(p_start, '%Y-%m-%d') if isinstance(p_start, str) else p_start
        self.p_end = DT.strptime(p_end, '%Y-%m-%d') if isinstance(p_end, str) else p_end
        if self.p_start > self.p_end:
            loger.error('NEW MODE: Period End is before the Period Start!')
            raise ValueError("period start should before period end!")
        # check rparg
        if isinstance(rparg, int):
            rparg = [rparg]
        elif isinstance(rparg, str):
            rparg = [int(_) for _ in rparg.replace(" ", "").split(",")]
        rparg.sort()
        # check and convert -1 to last day
        if rparg[0] < -1:
            raise ValueError("Value Not acceptable: %d" % rparg[0])
        if self.rpmode == self.__class__.RMODE_WEEKLY:
            if rparg[-1] > 7:
                raise ValueError("Value > 7 is Not acceptable on rparg!")
            if rparg[0] == -1:
                rparg.pop(0)
                if rparg[-1] != 7:
                    rparg.append(7)
        elif self.rpmode == self.__class__.RMODE_MONTHLY:
            if rparg[-1] > 31:
                raise ValueError("Value > 31 is Not acceptable on rparg!")
            if rparg[0] == -1:
                rparg.pop(0)
                rparg.append(-1)
        else:
            raise ValueError("Unkown rpmode!")
        i = 0
        for i in range(len(rparg)-1):
            if rparg[i] == rparg[i+1]:
                raise ValueError("dunplicate on rparg value![%d]" % rparg[i])
        self.rparg = rparg
        if isinstance(ontime, str):
            ontime = [int(_) for _ in ontime.split(":")]
            self.ontime = {'hour': ontime[0], 'minute': ontime[1], 'second': 0, 'microsecond': 0}
        else:
            self.ontime = {'hour': ontime.hour, 'minute': ontime.minute, 'second': 0, 'microsecond': 0}
        print(self.ontime)
        self.nextdtime = None

        if rpmode == self.__class__.RMODE_WEEKLY:
            if self.rparg[0] < 0 or self.rparg[-1] > 7:
                raise ValueError("week day defines not in [1,7]")
            self._weekly_hdl()
        elif rpmode == self.__class__.RMODE_MONTHLY:
            # extension: -1 as end month day
            if self.rparg[0] < -1 or self.rparg[-1] > 31:
                raise ValueError("week day defines not in [1,31]")
            self._monthly_hdl()
        else:
            raise ValueError("WRONG REPEAT MODE!")
        print(self)
        self.objid = None

    def _month_days(self, m, y):
        if m == 2:
            return 29 if y%400==0 or (y%4==0 and y%100!=0) else 28
        return self.__class__.MDAYS[m]

    def _weekly_hdl(self):
        now = DT.today()
        if now < self.p_start:
            now = self.p_start
        wd = now.isoweekday()
        getd = self.rparg[0]
        found = False
        for r in self.rparg:
            if r == -1:
                r = 7
            if r >= wd:
                found = True
                getd = r
                break
        if found is False:
            # not found the day after $wd in rparg, so go for next week's first rparg
            days = getd + 7 - wd
        else:
            # on this week
            days = getd - wd
        nextdtime = now + timedelta(days=days)
        self.nextdtime = nextdtime.replace(**self.ontime)

    def _monthly_hdl(self):
        now = DT.today()
        if now < self.p_start:
            now = self.p_start
        month_days = self._month_days(now.month, now.year)
        next_month_days = self._month_days(now.month+1, now.year)
        wd = now.day
        getd = self.rparg[0]
        if getd > next_month_days:
            raise ValueError("day to big to repeat!(%d on month %d)" % (getd, now.month))
        found = False
        for r in self.rparg:
            if r == -1:
                getd = month_days
                found = True
                print('get getd end of monthly: %d' % getd)
            if r >= wd:
                found = True
                getd = r
                print('get getd monthly: %d' % getd)
                break
        if found is False:
            # not found the day after $wd in rparg, so go for next month's first rparg
            days = month_days - wd + getd
        else:
            # on this month
            days = getd - wd
        nextdtime = now + timedelta(days=days)
        self.nextdtime = nextdtime.replace(**self.ontime)

    def _gonext(self, afterdate=None):
        afterdate = afterdate or self.nextdtime
        if self.rpmode != self.__class__.RMODE_ONCE and self.p_start > afterdate:
            loger.info("period after check date.")
            return
        if self.rpmode == self.__class__.RMODE_WEEKLY:
            # monday should be 1 (but in datetime is 0, if we not set datetime.firstweekday)
            # 默认情况下是当天onmeeting情况下（必然在rparg中）计算的，考虑到afterday可能是后一日甚至更后。。。
            # 应该用当前的nextdtime计算
            wd = afterdate.weekday() + 1
            i = self.rparg.index(wd)
            if i+1 == len(self.rparg):
                # next week
                td = self.rparg[0]
                od = td + 7 - wd
            else:
                td = self.rparg[i+1]
                od = td - wd
        elif self.rpmode == self.__class__.RMODE_MONTHLY:
            wd = afterdate.day
            i = self.rparg.index(wd)
            if i+1 == len(self.rparg):
                mdays = self._month_days(afterdate.month, afterdate.year)
                od = mdays - wd + self.rparg[0]
            else:
                od = self.rparg[i+1] - wd
        else:
            raise ValueError("WRONG RPMODE!")
        self.nextdtime = afterdate + timedelta(days=od)
        self.counting += 1
        print('nextdtime set: %s' % self.nextdtime)
    
    def update_nextdtime(self, new_datetime):
        # only for rpmode == 0
        if self.rpmode != 0:
            raise ValueError("ERROR: RPMODE != 0, when update_nextdtime!")
        if isinstance(new_datetime, str):
            self.nextdtime = DT.strptime(new_datetime, '%Y-%m-%d %H:%M:%S')
        elif isinstance(new_datetime, DT):
            self.nextdtime = new_datetime
        else:
            raise ValueError("ERROR: WRONG TYPE of new_datetime!")

    def update_rparg(self, new_rparg, rpmode=None):
        if rpmode and rpmode in (1, 2):
            self.rpmode = rpmode
        if isinstance(new_rparg, int):
            new_rparg = [new_rparg]
        new_rparg.sort()
        if self.rpmode == self.__class__.RMODE_WEEKLY:
            if new_rparg[0] < 0 or new_rparg[-1] > 7:
                raise ValueError("week day defines not in [1,7]")
            self.rparg = new_rparg
            self._weekly_hdl()
        elif self.rpmode == self.__class__.RMODE_MONTHLY:
            # extension: -1 as end month day
            if new_rparg[0] < -1 or new_rparg[-1] > 30:
                raise ValueError("week day defines not in [1,30]")
            self.rparg = new_rparg
            self._monthly_hdl()
        else:
            raise ValueError("WRONG REPEAT MODE!")

    def update_ontime(self, new_ontime):
        ontime = DT.strptime(ontime, '%H:%M:%S') if isinstance(ontime, str) else ontime
        self.onetime['hour'] = ontime.hour
        self.onetime['minute'] = ontime.minute
        self.onetime['second'] = ontime.second

    def update_x(self, **kwargs):
        for k,v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def set_objid(self, objid):
        self.objid = objid

    def set_announced(self):
        self.status = self.__class__.STA_ANNOUNCED

    def set_done(self):
        self.status = self.__class__.STA_DONE

    def set_over(self):
        self.status = self.__class__.STA_CLOSED

    def set_idle(self):
        # after update(writeback) to db
        self.status = self.__class__.STA_IDLE

    def force_update(self):
        self.status2 = self.__class__.STA2_FORCE_UPDATE

    def db_done(self):
        # write done status to db
        if self.status2 == self.__class__.STA2_TODAY_DONE:
            self.status2 = 0

    def set_updated(self):
        # when do writeback to db
        if self.status2 == self.__class__.STA2_FORCE_UPDATE:
            self.status2 = 0
        self.status = self.__class__.STA_IDLE

    def check(self, now=None):
        # check if current nextdtime, update status;
        # a) if before announce, pass
        # b) if before meeting and in announce time, trigger
        if not self.nextdtime:
            if self.rpmode == self.__class__.RMODE_WEEKLY:
                self._weekly_hdl()
            elif self.rpmode == self.__class__.RMODE_MONTHLY:
                self._monthly_hdl()
            else:
                raise ValueError("WRONG nextdtime")
        now = now or DT.now()
        # check p_end;已经过周期；回写到数据库；置为updated(待更新回写) + status2=OVERP
        if self.rpmode != self.__class__.RMODE_ONCE and self.p_end < now:
            print('p_end over: %s - %s' % (self.p_end, now))
            if self.status2 == self.__class__.STA2_OVERP:
                self.status = self.__class__.STA_USELESS
            else:
                self.status = self.__class__.STA_UPDATED
                self.status2 = self.__class__.STA2_OVERP
            return self.status
        # quickly judge if day diff over 1
        delta_date = self.nextdtime.day - now.day
        if delta_date > 1:
            self.status = self.__class__.STA_IDLE
            return self.status
        delta = self.nextdtime - now
        delta_days = delta.days
        # 注：dalta.days == 0指的是两个时间点差值小于24小时，因此当两个时间点尽管跨日(delta_date>=1)，但时间差小于24小时，则days依然为0
        # on day calculate for other status
        # mark:
        # datetime.datetime(2020, 1, 11, 10, 48, 9, 74871) - datetime.datetime(2020, 1, 11, 12, 48, 9, 74871) =>
        # datetime.timedelta(days=-1, seconds=79200); 79200//60//60 = 22 (24 - mtime)*60
        
        delta_minutes = delta.seconds // 60 if delta_days>=0 else 24*60-(delta.seconds//60)
        # MARK: if nextdtime after now, but less than 24h, delta.days = 0
        if delta_days < 0:
            # 已过开始时间,可能是当日，也可能是多日前(如果设置为手动结束会议，且未手动执行)
            # 单次会议直接结束
            if self.rpmode == self.__class__.RMODE_ONCE and self.status == self.__class__.STA_DONE:
                self.status = self.__class__.STA_USELESS
                return self.status
            # check if after/on meeting
            if self.status == self.__class__.STA_DONE:
                # 如果手动设置结束
                pass
            elif delta_minutes < self.mtime:
                self.status = self.__class__.STA_PROGRESSING
            elif self.__class__.AUTO_DONE is True:
                self.status = self.__class__.STA_DONE
                self.status2 = self.__class__.STA2_TODAY_DONE
            if delta_date < 0 and self.status != self.__class__.STA_UPDATED:
                # 跨日开始计算下一次会议；正常情况下一旦跨日变成00:00后会及时变更，故不作额外限制；
                # 更新后放入待回写列表，实时扫描队列在1：00后执行回写（此时如果正好有gonext行为则会因为回写导致丢失，因为
                # 回写后会清空列表）;如果出现问题，则应当在此处增加限制
                self._gonext()
                self.status = self.__class__.STA_UPDATED
                #self.__class__.update_sequence.append(self)
                #print('a meeting[%s] to be writeback...' % self.mid)
        elif delta_days == 0 and delta_date == 0:
            # onday&nextday and before
            if self.status == self.__class__.STA_ANNOUNCED:
                pass
            elif delta_minutes > self.announce:
                self.status = self.__class__.STA_ONDATE
            elif delta_minutes > 0:
                self.status = self.__class__.STA_ANNOUNCE
        else:
            # > 0
            self.status = self.__class__.STA_IDLE
        return self.status

    def check_date(self, date):
        # check meetings on date specified
        if self.rpmode == self.__class__.RMODE_ONCE:
            return self.mid if self.nextdtime.date() == date else None
        if self.rpmode == self.__class__.RMODE_WEEKLY:
            return self.mid if (date.weekday()+1) in self.rparg else None
        if self.rpmode == self.__class__.RMODE_MONTHLY:
            return self.mid if date.day in self.rparg else None

    def calendar(self, from_date=None, to_date=None, get_mode=0, withtime=False):
        # 周期性会议，某个阶段的日程表
        # 输出基于[from_date, ...,, to_date]的序列中有会议的index(即from_date到to_date的日期中第几日有会议)
        # get_mode: 0->idx, 1->datetime, 2->datetime-text
        from_date = from_date or self.p_start
        to_date = to_date or self.p_end
        days = (to_date - from_date).days
        if self.rpmode == self.__class__.RMODE_ONCE:
            _day = (self.nextdtime - from_date).days
            if  _day <= days:
                return [_day]
        export = []
        getd = lambda d: d.replace(**self.ontime) if withtime else d.date()
        if self.rpmode == self.__class__.RMODE_WEEKLY:
            test_range = self.rparg.copy()
            if test_range[-1] == 7:
                test_range[-1] = 0
            start_wd = from_date.weekday() + 1 # starts with 0
            for i in range(days+1):
                _wd = (i + start_wd) % 7
                if _wd in test_range:
                    export.append(_wd if get_mode==0 else getd(from_date + timedelta(days=i)) if get_mode==1 else str(getd(from_date + timedelta(days=i))))
        if self.rpmode == self.__class__.RMODE_MONTHLY:
            test_range = [0]*32 # from 1, so test_range[0] will be ignore, and if -1, [31] will be set
            for i in self.rparg:
                # if -1, test_range[31] == 1
                test_range[i] = 1
            _cur_month = 0
            _mdays = 0
            for i in range(days+1):
                _d = from_date + timedelta(days=i)
                if _cur_month != _d.month:
                    _cur_month = _d.month
                    # 月份变化, next month, 判断是否需要填入月末数值
                    if _mdays > 0:
                        test_range[_mdays] -= 99
                    if _cur_month == 12:
                        _mdays = self._month_days(_cur_month, _d.year-1)
                    else:
                        _mdays = self._month_days(_cur_month, _d.year)
                    test_range[_mdays] += 99
                if test_range[_d.day] >= 1:
                    export.append(i if get_mode==0 else getd(_d) if get_mode==1 else str(getd(_d)))
        return export

    @staticmethod
    def calendar2(rpmode, rparg, from_date, to_date, get_mode=0):
        # 周期性会议，某个阶段的日程表；生成会议日历
        # 输出基于[from_date, ..., to_date]的序列中有会议的index(即from_date到to_date的日期中第几日有会议)
        # get_mode: 0->idx, 1->datetime, 2->datetime-text
        def _month_days(m, y):
            if m == 2:
                return 29 if y%400==0 or (y%4==0 and y%100!=0) else 28
            return mnode.MDAYS[m]
        from_date = from_date if isinstance(from_date, DT) else DT.strptime(from_date, '%Y-%m-%d')
        to_date = to_date if isinstance(to_date, DT) else DT.strptime(to_date, '%Y-%m-%d')
        export = []
        days = (to_date - from_date).days
        if rpmode == mnode.RMODE_WEEKLY:
            test_range = rparg.copy()
            if test_range[-1] == 7:
                test_range[-1] = 0
            start_wd = from_date.weekday() + 1 # starts with 0
            for i in range(days+1):
                _wd = (i + start_wd) % 7
                if _wd in test_range:
                    export.append(_wd if get_mode==0 else (from_date + timedelta(days=i)).date() if get_mode==1 else str((from_date + timedelta(days=i)).date()))
        if rpmode == mnode.RMODE_MONTHLY:
            test_range = [0]*32 # from 1, so test_range[0] will be ignore, and if -1, [31] will be set
            for i in rparg:
                # if -1, test_range[31] == 1
                test_range[i] = 1
            _cur_month = 0
            _mdays = 0
            for i in range(days+1):
                _d = from_date + timedelta(days=i)
                if _cur_month != _d.month:
                    _cur_month = _d.month
                    # 月份变化, next month, 判断是否需要填入月末数值
                    if _mdays > 0:
                        test_range[_mdays] -= 99
                    if _cur_month == 12:
                        _mdays = _month_days(_cur_month, _d.year-1)
                    else:
                        _mdays = _month_days(_cur_month, _d.year)
                    test_range[_mdays] += 99
                if test_range[_d.day] >= 1:
                    export.append(i if get_mode==0 else _d.date() if get_mode==1 else str(_d.date()))
        return export

    def conflic_mode0(self, mroom, ondate, t_s, t_e):
        # 查找一次性会议中是否存在时间冲突的[同一个会议室]
        # return self.mid if conflic
        # t_s: time_int of start_meeting
        # t_e: time_int of end_meeting == time_int of start_meeting + meetingtime(minute)
        if self.rpmode == self.__class__.RMODE_ONCE and self.nextdtime.date() == ondate:
            _ts = self.nextdtime.hour * 60 + self.nextdtime.minute
            _te = _ts + self.mtime
            if (t_s<_ts<t_e or t_s<_te<t_e):
                return self.mid
        return 0

    def __repr__(self):
        return '会议(%s) on[%s] in<%s>: %s' % (self.name, self.nextdtime, self.mroom, self.__class__.STA_TEXT[self.status])


class Mqueue(object):
	# Meeting queue.
	# in memory, realtime
	# list-node: mnode
    datalimit = 1024

    #glock = Lock()
    stimer = None
    stimer_flag = True
    sync_interval = 60
    sync_count = 0
    ins_queues = {}
    ins_limit = 10

    slock_itv = 0.1
    slock_times = 10

    @classmethod
    def set_period(cls, begin_date, end_date):
        cls.period_begin = begin_date
        cls.period_end = end_date

    @classmethod
    def set_announcer(cls, anncer):
        # BECARE: after announce, node should call node.set_announced()
        # announcer(i.ikey, i.announce): ikey to identifed the queue instance, announce: list to announce
        def _ann(ann_q):
            print(ann_q)
            alen = len(ann_q)
            for _ in range(alen):
                n = ann_q.pop(0)
                print('emurate announce on: %d done!' % n.mid)
                n.set_announced()
        if callable(anncer):
            cls.announcer = anncer
        else:
            cls.announcer = _ann

    @classmethod
    def set_dbwritebacker(cls, dbwritebacker):
        # 设置回写器，异步调用
        def _dbw(l):
            print(l)
            for _ in l:
                print('emurate dbwriteback on: %d done!' % _.mid)
                _.set_idle()
            mnode.clear_update_sequence()
        if callable(dbwritebacker):
            cls.dbwritebacker = dbwritebacker
        else:
            cls.dbwritebacker = _dbw

    @classmethod
    def set_synctime(cls, synctime=0):
        synctime = synctime or cls.sync_interval
        if synctime < 30:
            logging.warning("synctime less then 30, and fix to 30s.")
            synctime = 30
        elif synctime > 60:
            logging.warning("synctime too long, and fix to 60s.")
        cls.sync_interval = synctime
        cls.sync_timer()

    @classmethod
    def sync_timer(cls):
        if cls.stimer_flag is False:
            loger.warning("sync stop!")
            cls.stimer.cancel()
            return
        if len(cls.ins_queues) > cls.ins_limit:
            logging.warning("lsourcer instance too many (over %s)!" % cls.ins_limit)
        #loger.info("stating syncs ...<%s>" % DT.now())
        for i in cls.ins_queues.values():
            if i._scan():
                #loger.info("finish scan for %s" % i.name)
                #cls.announcer(i.ikey, i.announce)
                pass
            else:
                loger.error("scan %s failure!" % i.name)
        # annouce:
        if len(mnode.announce_sequence) > 0:
            loger.info("go for announce!")
            if issubclass(cls.announcer, Thread):
                _th = cls.announcer(mnode.announce_sequence)
                _th.start()
            elif callable(cls.announcer):
                # cls.announcer(mnode.update_sequence)
                _th = Thread(target=cls.announcer, args=(mnode.announce_sequence,))
                _th.start()
        # db writeack when mnode.update_sequence > 0
        #if len(mnode.update_sequence) > 0 and time.localtime().tm_hour != 1 and mnode.wb_day<time.localtime().tm_day:
        if len(mnode.update_sequence) > 0:
            loger.info("go for dbwriteback!")
            if issubclass(cls.dbwritebacker, Thread):
                _th = cls.dbwritebacker(mnode.update_sequence)
                _th.start()
            elif callable(cls.dbwritebacker):
                # cls.dbwritebacker(mnode.update_sequence)
                _th = Thread(target=cls.dbwritebacker, args=(mnode.update_sequence,))
                _th.start()
            mnode.wb_day(time.localtime().tm_mday)
        cls.sync_count += 1
        cls.stimer = Timer(cls.sync_interval, cls.sync_timer)
        cls.stimer.start()
        #print("starting timer for sync... with interval %s" % cls.sync_interval)

    @classmethod
    def stop_syc(cls):
        if cls.stimer and cls.stimer.is_alive():
            cls.stimer.cancel()

    @classmethod
    def get_queue(cls, ikey, autonew=True):
        if ikey not in cls.ins_queues and autonew is True:
            queue = cls(ikey)
        return cls.ins_queues[ikey]

    @classmethod
    def auto_node(cls, ikey, anode, name=None):
        if ikey in cls.ins_queues:
            return cls.ins_queues[ikey].add_node(anode)
        else:
            new_q = cls(ikey, name)
            return new_q.add_node(anode)

    def __init__(self, ikey, name=None, enable=True):
        # queue instance
        if len(self.__class__.ins_queues) >= self.__class__.ins_limit:
            raise RuntimeError("No more queue allowed! and the queue limit is: [%d]" % self.__class__.ins_limit)
        self.name = name or ikey
        self.ikey = ikey
        self._nodes = []
        self.scan_lock = False
        self.enable = enable
        self.__class__.ins_queues[ikey] = self

    def __iter__(self):
        for node in self._nodes:
            yield node

    def __contains__(self, mid):
        for n in self._nodes:
            if n.mid == mid:
                return True
        return False

    def __getitem__(self, mid_mname):
        if isinstance(mid_mname, int):
            for n in self._nodes:
                if n.mid == mid_mname:
                    return n
        elif isinstance(mid_mname, str) and not mid_mname.isdigit():
            for n in self._nodes:
                if n.name == mid_mname:
                    return n

    def _scan(self, check_dtime=None):
        # is there a meeting to ANNOUNCE
        if self.scan_lock is True:
            loger.error("scan_lock is locked! when scan;")
            return False
        self.scan_lock = True
        #loger.debug("%s scan start..." % self.name)
        check_dtime = check_dtime or DT.now()
        i = 0
        useless = []
        self.scantime = check_dtime
        for node in self._nodes:
            rt = node.check(check_dtime)
            # 更新状态// sta_done 也要回写
            #print(node)
            if rt == mnode.STA_USELESS or rt == mnode.STA_CLOSED:
                useless.append(i)
            elif rt == mnode.STA_ANNOUNCE:
                print('a meeting[%s] to be announce...' % node.mid)
                node.set_objid(self.ikey)
                mnode.announce_sequence.append(node)
            elif node.status2 == mnode.STA2_FORCE_UPDATE  or node.status2 == mnode.STA2_TODAY_DONE or rt == mnode.STA_UPDATED:
                print('a meeting[%s] to be writeback...' % node.mid)
                mnode.update_sequence.append(node)
            i += 1
        if len(useless) > 0:
            print('useless exists, clear.')
            useless.sort()
            useless.reverse()
            for _ in useless:
                self._nodes.pop(_)
        self.scan_lock = False
        return True

    def add_node(self, node=None, **kwargs):
        # if check for conflic is OK, add node and return True to allow (insert into db)
        if self.scan_lock is True:
            raise RuntimeError("mlist is locked!")
        if node is None:
            mid = kwargs.pop('mid')
            try:
                node = mnode(mid, **kwargs)
            except ValueError:
                return None
        else:
            for n in self._nodes:
                if n.mid == node.mid:
                    return node
        if node.mid > 0:
            self._nodes.append(node)
            return node
        else:
            loger.error("node with mid not > 0!")
            return None

    def add_nodes(self, nodes):
        if self.scan_lock is True:
            raise RuntimeError("mlist is locked!")
        if isinstance(nodes[0], mnode):
            for n in nodes:
                self.add_node(n)
        elif isinstance(nodes[0], dict):
            for n in nodes:
                self.add_node(**n)

    def remove(self, node_key):
        # wait for scan lock
        wtimes = 30
        while wtimes > 0:
            wtimes -= 1
            if self.scan_lock is False:
                break
        if wtimes <= 0:
            #raise RuntimeError("Blocked by scan lock!")
            loger.error("Blocked by scan lock!")
            return False
        if isinstance(node_key, (str, int)):
            for n in self._nodes:
                if n.mid == node_key:
                    self._nodes.remove(n)
        elif isinstance(node_key, mnode):
            try:
                self._nodes.remove(node_key)
            except:
                pass
        else:
            loger.error("unknown node_key/node!")
        return True

    def node_update_rparg(self, mid, new_rparg, rpmode=None):
        # 未来功能，从queue更新node，使得node的更新可控，直接反应到队列的更新，从而实现缓存
        raise NotImplementedError

    def node_update_rpmode(self, new_ontime):
        # 未来功能，从queue更新node，使得node的更新可控，直接反应到队列的更新，从而实现缓存
        raise NotImplementedError

    def filter_queue(cls, ikey, by_rpmode=-1, by_mroom=-1, filter_func=None):
        # 查找特定类型的会议：会议类型，会议室，筛选函数
        # 输出列表
        export = []
        for i in self._nodes:
            if by_rpmode >= 0 and i.rpmode != by_rpmode:
                continue
            elif by_mroom >= 0 and i.mroom != by_mroom:
                continue
            elif filter_func and filter_func(i) is False:
                continue
            export.append(i)
        return export

    def filter_room_conflict_once(self, mroom, ondate, ontime, mtime):
        # 查找 指定会议室 在 指定的时间 是否存在冲突的【一次性会议】 
        ondate = (ondate if isinstance(ondate, DT) else DT.strptime(ondate, '%Y-%m-%d')).date()
        h_m = str(ontime)[:5].split(':')
        t_s = int(h_m[0]) * 60 + int(h_m[1])
        t_e = t_s + mtime
        for i in self._nodes:
            mid = i.conflic_mode0(mroom, ondate, t_s, t_e)
            if mid:
                return mid
        return 0

    def filter_room_conflict(self, rpmode, rparg, mroom, ontime, mtime, p_start, p_end):
        # check for conflict room：
        # 在给定的时间段【学期？】内，是否有和指定参数的会议【开始时间，会议长度，会议室，会议类型，会重复参数】冲突的会议
        # return mid if conflict else None
        # ontime: datetime.time => int
        # mtme: minute int
        # 返回冲突的“第一个”会议id，返回0表示无冲突【冲突的会议编号为0】
        def t_conflict(_dt, _mtime):
            # conflict will return True
            _ts = _dt.hour * 60 + _dt.minute
            _te = _ts + _mtime
            return (t_s < _ts < t_e) or (t_s < _te < t_e)
        def t_conflict2(_dt, _mtime):
            # conflict will return True
            _ts = _dt['hour'] * 60 + _dt['minute']
            _te = _ts + _mtime
            return (t_s < _ts < t_e) or (t_s < _te < t_e)
        p_start = p_start if isinstance(p_start, DT) else DT.strptime(p_start, '%Y-%m-%d')
        p_end = p_end if isinstance(p_end, DT) else DT.strptime(p_end, '%Y-%m-%d')
        check_schedule = mnode.calendar2(rpmode, rparg, p_start, p_end, get_mode=1)
        if not check_schedule:
            raise ValueError("no calendar from params!")
        #use int for comparing
        h_m = str(ontime)[:5].split(':')
        t_s = int(h_m[0]) * 60 + int(h_m[1])
        t_e = t_s + mtime
        for i in self._nodes:
            print('comparing %s...' % str(i))
            if i.mroom == 0 or i.mroom != mroom:
                continue
            elif i.rpmode == mnode.RMODE_ONCE:
                if t_conflict(i.nextdtime, i.mtime):
                    return i.mid
                continue
            elif t_conflict2(i.ontime, i.mtime):
                return i.mid
            elif i.p_end < p_start or i.p_start > p_end:
                continue
            _p_start = p_start if p_start > i.p_start else i.p_start
            _p_end = p_end if p_end < i.p_end else i.p_end
            for d in check_schedule:
                check_schedule2 = i.calendar(from_date=_p_start, to_date=_p_end, get_mode=1)
                for _d in check_schedule2:
                    if d == _d:
                        print("conflic_meeting %s on date: %s" % (i.name, d))
                        return i.mid
        return 0

    def calendar(self, from_date=None, to_date=None, emode=0):
        from_date = from_date or self.__class__.period_begin
        to_date = to_date or self.__class__.period_end
        days = (to_date - to_date).days
        if days < 0:
            raise ValueError("%s-%s period wrong!" % (from_date, to_date))
        # PY3
        c_array = [str(from_date + timedelta(days=i)) for i in range(days)]
        v_array = [None]*days
        for i in range(days):
            export[str(from_date + timedelta(days=i))] = None
        for n in self._nodes:
            darray = n.calendar(from_date, to_date)
            if len(darray) == 0:
                continue
            for d in darray:
                if v_array[d] is None:
                    v_array[d] = []
                v_array[d].append(n.mid)
        if emode == 0:
            # [None, None, [mid1, mid2, ...], ...]
            return v_array
        elif emode == 1:
            # {day1_txt: None, ..., dayn_txt: [mid1, mid2, ...], ...}
            export = dict.from_keys(c_array)
            c = 0
            for c in range(days):
                if v_array[c]:
                    export[c_array[c]] = v_array[c]
            return export

    def calendar_month_week(self, year=0, month=0, week=None):
        # {day1_txt: None, ..., dayn_txt: [mid1, mid2, ...], ...}
        if year == 0 or month == 0:
            d = DT.today()
            year = year or d.year
            month = month or d.month
        month_dates =  calendar.Calendar(firstweekday=1).monthdatescalendar(year, month)
        export = {}
        if isinstance(week, int) and 0<=week<=6:
            target = month_dates(week)
            for date in target:
                checkd = []
                for n in self._nodes:
                    rt = n.check_date(date)
                    if rt:
                        checkd.append(rt)
                if len(checkd) > 0:
                    export[str(date)] = checkd
        else:
            for target in month_dates:
                for date in target:
                    checkd = []
                    for n in self._nodes:
                        rt = n.check_date(date)
                        if rt:
                            checkd.append(rt)
                    if len(checkd) > 0:
                        export[str(date)] = checkd

    def today(self, req_date=None, take_node=False):
        # 当日会议
        req_date = req_date or DT.today().date()
        rt = []
        for n in self._nodes:
            mid = n.check_date(req_date)
            if mid:
                rt.append(n)
        # sorted
        rt = sorted(rt, key=lambda _:_.nextdtime)
        if take_node:
            rt
        else:
            return [_.mid for _ in rt]

    def next_m(self, check_dtime=None):
        # 确认指定时间之后的最近一次会议
        # 0 则当日无会议; 无意义；应当基于用户
        check_dtime = check_dtime or DT.now()
        min_seconds = 86399
        mid = 0
        for n in self._nodes:
            delta = n.nextdtime - check_dtime
            if delta.day == 0 and delta.seconds < min_seconds:
                min_seconds = delta.seconds
                mid = n.mid
        return mid


if __name__ == '__main__':
    # test single:
    p_s = '2020-02-01'
    p_e = '2020-08-31'
    m1 = mnode(1, 'meeting1', mroom=1, ondate='2020-02-15', ontime='12:00:00')
    m2 = mnode(2, 'meeting2', mroom=2, rpmode=1, rparg=1, ontime='12:00:00', p_start=p_s, p_end=p_e)
    m3 = mnode(3, 'meeting3', mroom=3, rpmode=1, rparg=[1,4,7], ontime='13:30:00', p_start=p_s, p_end=p_e)
    m4 = mnode(4, 'meeting4', mroom=2, rpmode=2, rparg=[10, 20, -1], ontime='14:00:00', p_start=p_s, p_end=p_e)
    m5 = mnode(5, 'meeting5', mroom=3, rpmode=2, rparg=[1, -1, 6, 20], ontime='15:00:00', p_start=p_s, p_end=p_e)
    m6 = mnode(6, 'meeting6', mroom=3, ondate='2020-02-14', ontime='18:35:00', mtime=5)
    ms = [m1, m2, m3, m4, m5, m6]
    for m in ms:
        print(m.nextdtime)
    _d0 = DT.strptime('2020-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    _d1 = DT.strptime('2020-03-31 23:59:59', '%Y-%m-%d %H:%M:%S')
    print(m3.calendar(_d0, _d1, get_mode=2))
    print(m4.calendar(_d0, _d1, get_mode=2, withtime=True))
    print(m5.calendar(_d0, _d1, get_mode=2, withtime=True))
    print(m5.rparg)
    q1 = Mqueue('ikey1', 'group1')
    q2 = Mqueue('ikey2', 'group2')
    q1.add_nodes(ms)
    mnode.update_sequence.append(m4)
    Mqueue.set_announcer(None)
    Mqueue.set_dbwritebacker(None)
    x_mid = q1.filter_room_conflict(1, [2,3], 2, '13:00:00', 120, '2020-04-01', '2020-09-30')
    print('conflict found: %d' % x_mid if x_mid else 'conflict not found!')
    #Mqueue.sync_timer()