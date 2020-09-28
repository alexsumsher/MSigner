#!/usr/bin/env python
# -*- coding: utf8

"""
working wxcampus server
update: keyId for secure school
"""
import time

from libs import binfile
from tschool import appmsg_sets, appmsg_sets2, capp_smsg, thirdsvr2, assist_svr
from modules import sysconsts
from ultilities import dict_search2, dict_search3
from sys_config import cur_config, loger
from actions import on_school
#from cur_config_test import cur_config, logging

class app_school(thirdsvr2):
    token = cur_config.app_token

    def __init__(self, objid):
        self.token = {}
        for key in thirdsvr2.token:
            self.token[key] = self.__class__.token[key]
        super(app_school, self).__init__()
        self.token['objectid'] = objid


#class myschool(thirdsvr2):
class myschool(assist_svr):
    SCHOOLS = {}
    #token = thirdsvr2.gen_token(cur_config.token())  devCode+devType+keyId

    """myschool, comunicate with tencent smart school"""
    # seperator with mysql data table
    
    @classmethod
    def settoken(cls, token):
        cls.token = {}
        for k in assist_svr.token:
            cls.token[k] = token[k]
        print(cls.token)

    @classmethod
    def myschool(cls, objid, chkable=False):
        if objid in cls.SCHOOLS:
            return cls.SCHOOLS[objid]
        else:
            _school = cls(objid, chkable=chkable)
            cls.SCHOOLS[objid] = _school
            keyset = on_school('keyid-get', objid)
            if keyset:
                _school.svr_key = keyset[0]
                _school.token['keyId'] = keyset[1]
                print("a key set found!")
            return _school

    def __init__(self, school_objid, chkable=False, keyid=None, token=None):
        # student_department;
        # teacher_department;
        if token:
            self.token = token.copy()
        else:
            self.token = self.__class__.token.copy()
        self.token['objectid'] = school_objid
        # append keyid
        if keyid:
            self.token['keyId'] = keyid
        super(myschool, self).__init__()
        self.objid = school_objid
        if chkable:
            sinfo = self.schoolinfo()
            print(sinfo)
            if sinfo['code'] != 0:
                raise ValueError("check school failure: %s" % sinfo['msg'])

    @property
    def name(self):
        realurl = self.handle_msger()
        with capp_smsg('get_schoolinfo') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            n = wx_rtdata['data']['name']
        else:
            n = None
        return n

    def __simple_geter(self, reqname, reqid=None):
        realurl = self.handle_msger()
        wx_rtdata = None
        with capp_smsg(reqname) as qer:
            wx_rtdata = qer.get(urlpath=realurl, force=True)
        if reqid and wx_rtdata['code'] == 0:
            return wx_rtdata['data']['dataList'].get(reqid)
        return wx_rtdata
    
    # collect datas from tencent server
    def col_schoolyear(self, syid=None):
        return self.__simple_geter('get_schoolyears').get('data')

    def col_schoolterm(self, termid=None):
        return self.__simple_geter('get_schoolterm').get('data')

    def col_course(self, cid=None):
        return  self.__simple_geter('get_courseinfo').get('data')

    def schoolinfo(self):
        realurl = self.handle_msger()
        with capp_smsg('get_schoolinfo') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return wx_rtdata['data']
        return wx_rtdata

    def col_grades(self, dpid=None):
        student_departments = self.col_departments(1)
        if not student_departments:
            return None
        if not dpid:
            return dict_search2(student_departments['data'], 'departid', dpid)
        else:
            return dict_search2(student_departments['data'], 'level', '5')

    def col_classes(self, dpid=None):
        student_departments = self.col_departments(1)
        if not student_departments:
            return None
        if not dpid:
            return dict_search2(student_departments['data'], 'departid', dpid)
        else:
            return dict_search2(student_departments['data'], 'level', '6')

    def col_teacher_class(self, userid, ftype=0):
        # class that teach
        # 3:teach; 2:classteacher; 1-classmanager
        reqd = {'userid': userid}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_teacherclass') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            if ftype and 0<ftype<4:
                return dict_search2(wx_rtdata['data'], 'type', str(ftype))
            else:
                return wx_rtdata['data']
        return wx_rtdata

    def col_class_students(self, classid, page=1, page_limit=100):
        reqd = {'usertype': 1, 'departid': classid, 'level': 6, 'page': page, 'pageSize': page_limit}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_users') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        return wx_rtdata

    def col_dep_tearchers(self, dpid, level, page=1, page_limit=100, takeall=False):
        # 获取某个部门的老师
        reqd = {'usertype': 2, 'departid': dpid, 'level': level, 'page': page, 'pageSize': page_limit}
        counts = 100 if takeall else 2
        teachers = []
        wx_rtdata = None
        total = 0
        for x in range(1, counts):
            reqd['page'] = x
            realurl = self.handle_msger(reqs=reqd)
            with capp_smsg('get_users') as qer:
                wx_rtdata = qer.get(urlpath=realurl)
            if wx_rtdata['code'] == 0:
                teachers.extend(wx_rtdata['data']['dataList'])
                total += len(wx_rtdata['data']['dataList'])
                if len(wx_rtdata['data']['dataList']) < page_limit:
                    loger.info("users with total: %s" % total)
                    break
            else:
                break
            time.sleep(0.2)
        return teachers

    def col_departments(self, utype=1):
        # base on stduent
        reqd = {'usertype': utype}
        realurl = self.handle_msger(reqs=reqd)
        with capp_smsg('get_dpinfos') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return wx_rtdata['data']
        else:
            loger.warning("take department failure[%s]" % wx_rtdata['msg'])
            return None

    def check_dp(self, dpid, exists=False):
        reqd = {'departid': dpid}
        realurl = self.handle_msger(reqs=reqd)
        with capp_smsg('get_dptinfobyId') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            if exists:
                return True
            else:
                return wx_rtdata['data']
        loger.warning("get department wrong!")
        return wx_rtdata

    def get_teacher_inidata(self, userid):
        # 获取教师信息及其管理班级
        reqd = {'userid': userid}
        inidata = {}
        with capp_smsg('get_userinfo') as qer:
            realurl = self.handle_msger(reqs=reqd)
            userdatas = qer.get(urlpath=realurl)
        if int(userdatas['code']) == 0:
            inidata['code'] = 0
            inidata['msg'] = userdatas['msg']
            inidata['datetime'] = userdatas['datetime']
            inidata['user_info'] = userdatas['data']
        else:
            return userdatas
        with capp_smsg('get_teacherclass') as qer:
            realurl = self.handle_msger(reqs=reqd)
            classesdata = qer.get(urlpath=realurl)
        if int(classesdata['code']) == 0:
            inidata['user_classes'] = classesdata['data']
        return inidata

    def get_user(self, userid, ck_admin=False):
        reqd = {'userid': userid}
        userdatas = None
        with capp_smsg('get_userinfo') as qer:
            realurl = self.handle_msger(reqs=reqd)
            userdatas = qer.get(urlpath=realurl)
        if ck_admin and userdatas['code'] == 0:
            with capp_smsg('get_admininfo') as qer:
                realurl = self.handle_msger(reqs=reqd)
                admininfo = qer.get(urlpath=realurl)
                userdatas['admininfo'] = admininfo
        return userdatas