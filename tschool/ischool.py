#!/usr/bin/env python
# -*- coding: utf8

"""
working wxcampus server
"""
import time

from libs import binfile
import appmsg_sets, appmsg_sets2, capp_smsg, selfserver
from modules import sysconsts
from ultilities import dict_search2, dict_search3
from sys_config import cur_config, logging
from actions import on_school
#from cur_config_test import cur_config, logging
loger = logging.getLogger()


class myschool(selfserver):

    """myschool, comunicate with tencent smart school"""
    teacher_course_mapping = {}
    grade_subjects = None
    SCHOOLS = {}
    # grade_subject: {gradeid: [subjectid1, subjectid2, ...], ...}
    
    @classmethod
    def get_top2(cls, schooldata):
        # get top departmentid by type2 (student)
        pass
    
    @classmethod
    def myschool(cls, dpid, tokens=None, **ext_token):
        if dpid in cls.SCHOOLS:
            return cls.SCHOOLS[dpid]
        elif tokens:
            _school = cls(tokens, **ext_token)
            return _school
    
    @property
    def name(self):
        n = self.basic_info.get('name')
        if not n:
            realurl = self.handle_msger()
            with capp_smsg('get_schoolinfo') as qer:
                wx_rtdata = qer.get(urlpath=realurl)
            if wx_rtdata['code'] == 0:
                self.basic_info['name'] = n = wx_rtdata['data']['name']
            return n
        return ""

    def __init__(self, tokens, data_struct=None, **ext_token):
        super(myschool, self).__init__(tokens, **ext_token)
        self.basic_info = {
            'cur_yearid': None,
            'cur_yearname': "",
            'cur_termid': None,
            'top_departid': None
        }
        if data_struct:
            self.schooldata = data_struct
        else:
            dps = self.col_departments()
            if dps is not None:
                self.schooldata = dps
                self.mainid = dict_search2(dps, 'level', '1', one=True)
            else:
                raise RuntimeError("can not inital school!")

    def _class_2_grade(self):
        if isinstance(classid, dict):
            clsid = classid['departid']
            gid = clsid['parentid']
            grade = dict_search2(self.schooldata, 'departid', gid)
            return grade
        grades = dict_search2(self.schooldata, 'level', '5')
        if not grades:
            return None
        for g in grades:
            for c in g['child']:
                if c['departid'] == classid:
                        return g
        return None

    def _list_class(gradeid=""):
        if not gradeid:
            return dict_search2(self.schooldata, 'level', '6')
        grade = dict_search2(self.schooldata, 'departid', gradeid, one=True)
        return grade['child'] if isinstance(grade, dict) and 'child' in grade else None

    def school(self):
        realurl = self.handle_msger()
        with capp_smsg('get_schoolinfo') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return wx_rtdata['data']
        return ""

    def __simple_geter(self, reqname, reqid=None):
        realurl = self.handle_msger()
        wx_rtdata = None
        with capp_smsg(reqname) as qer:
            wx_rtdata = qer.get(urlpath=realurl, force=True)
        if reqid and wx_rtdata['code'] == 0:
            return wx_rtdata['data']['dataList'].get(reqid)
        return wx_rtdata

    def _getclass_s(clsid_s, gradeid=None, take=None):
        # take more then one class for a faterway
        # clsid_s: [clsid, clsid, ...]
        # if gradeid: find in grade
        clslist = clsid_s if isinstance(clsid_s, (list, tuple)) else [_.strip() for _ in clsid_s.split(',')]
        source = dict_search2(self.schooldata, 'departid', gradeid, one=True) if gradeid else holder.ss
        result = dict_search3(source, 'departid', clslist, listout=False, outkey='departid')
        if not take:
            return result
        out = {}
        for k,v in result.items():
            out[k] = v[take]
        return out
    
    # collect datas from tencent server
    def col_schoolyear(self, syid=None):
        return self.__simple_geter('get_schoolyears').get('data')

    def col_schoolterm(self, termid=None):
        return self.__simple_geter('get_schoolterm').get('data')

    def col_course(self, cid=None):
        return  self.__simple_geter('get_courseinfo').get('data')

    def col_grades(self):
        reqd = {'usertype': 1}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_dpinfos') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return dict_search2(wx_rtdata['data'], 'level', '5')
        return wx_rtdata

    def col_classes(self):
        reqd = {'usertype': 1}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_dpinfos') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return dict_search2(wx_rtdata['data'], 'level', '6')
        return wx_rtdata

    def col_teacher_class(self, userid, ftype=3):
        # class that teach
        # 3:teach; 2:classteacher; 1-classmanager
        reqd = {'userid': userid}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_teacherclass') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            return dict_search2(wx_rtdata['data'], 'type', str(ftype))
        return wx_rtdata

    def col_class_students(self, classid, page=1, page_limit=100):
        reqd = {'usertype': 1, 'departid': classid, 'level': 6, 'page': page, 'pageSize': page_limit}
        realurl = self.handle_msger(reqs=reqd)
        wx_rtdata = None
        with capp_smsg('get_users') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        return wx_rtdata

    def col_dep_tearchers(self, dpid, level, page=1, page_limit=100, takeall=False):
        reqd = {'usertype': 2, 'departid': dpid, 'level': level, 'page': page, 'pageSize': page_limit}
        counts = 100 if takeall else 1
        teachers = []
        wx_rtdata = None
        for x in xrange(counts):
            reqd['page'] = x
            realurl = self.handle_msger(reqs=reqd)
            with capp_smsg('get_users') as qer:
                wx_rtdata = qer.get(urlpath=realurl)
            if wx_rtdata['code'] == 0:
                teachers.extend(wx_rtdata['data']['dataList'])
            if wx_rtdata['data']['pageInfo']['page'] == wx_rtdata['data']['pageInfo']['total']:
                break
            time.sleep(0.2)
        if takeall:
            return teachers
        return wx_rtdata

    def col_departments(self, utype=1):
        # base on stduent
        reqd = {'usertype': utype}
        realurl = self.handle_msger(reqs=reqd)
        with capp_smsg('get_dpinfos') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0:
            if utype == 1:
                self.__class__.lasttime['school_struct1'] = time.time()
            return wx_rtdata['data']
        else:
            return None

    def get_gradestruct_byschooldata(self):
        if self.schooldata:
            self.__class__.lasttime['school_struct1'] = time.time()
            top = dict_search2(self.schooldata, 'departid', self.mainid, one=True)
            return top['child'] if top else None

    def check_dp(self, dpid, exists=False):
        reqd = {'departid': dpid}
        realurl = self.handle_msger(reqs=reqd)
        with capp_smsg('get_dptinfobyId') as qer:
            wx_rtdata = qer.get(urlpath=realurl)
        if wx_rtdata['code'] == 0 and exists:
            return True
        return wx_rtdata

    def get_teacher_inidata(self, userid):
        # get teachers infomation and whos' class
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

    def get_teacher_grades(self, userid, termid):
        # it's so bad, for we could not take a teachers' teaching grades
        # get: [{course1: [gid1, gid2...]}, course2: [gid1, gid2]]
        reqd = {'teacherid': userid, 'term_id': termid}
        with capp_smsg('get_teacherscheduel') as qer:
            realurl = self.handle_msger(reqs=reqd)
            schedueldata = qer.get(urlpath=realurl)
        if int(schedueldata['code']) == 0:
            courselist = {}
            for _ in schedueldata['data']:
                the_course = None
                for cid,course in courselist.iteritems():
                    if _['course_id'] == cid:
                        the_course = course
                        break
                if the_course is None:
                    #the_course = {'course_id': _['course_id'], 'grades': []}
                    the_course = []
                    courselist[_['course_id']] = the_course
                g = self._class_2_grade(_['classid'])
                if not g or g['departid'] in the_course:
                # elif g['departid'] in [g['departid'] for g in the_course['grades']]
                    continue
                the_course.append(g['departid'])
            return courselist

    def get_teacher_cct(self, teacherid, termid, courseid):
        reqd = {'teacherid': teacherid, 'term_id': termid}
        with capp_smsg('get_teacherscheduel') as qer:
            realurl = self.handle_msger(reqs=reqd)
            schedueldata = qer.get(urlpath=realurl)
        if int(schedueldata['code']) == 0:
            clss = []
            for _ in schedueldata['data']:
                if _['course_id'] == courseid:
                    clss.append(_['classid'])
            return self._getclass_s(clss, take='departname')

    def cls_tchr_course(self, termid):
        # collect all tearchers
        # collect all class, class's course
        # export: c_c_t: {classid: {classname, courseid, teacherid, teachername}}
        # c_c_t: {classid: {classname, courseid: {teacherid, teachername}, ...}}
        # TODO: use time cacher
        teachers = {}
        reqd = {'usertype': 2, 'page': 0, 'pageSize': 100, 'departid': self.mainid, 'level': 1}
        with capp_smsg('get_users') as qer:
            for _ in xrange(1, 6):
                reqd['page'] = _ 
                realurl = self.handle_msger(reqs=reqd)
                srt = qer.get(urlpath=realurl)
                if not srt or srt['code'] != 0:
                    break
                #teachers.extend(srt['data']['dataList'])
                for t in srt['data']['dataList']:
                    teachers[t['userid']] = t['name']
        if len(teachers) == 0:
            print "no teacher founld!"
            return None
        print teachers
        classes = self._list_class()
        print "classes count: %s" % len(classes)
        c_c_t = {}
        for cc in classes:
            clsid = cc['departid']
            c_c_t[clsid] = dict(classname=cc['departname'])
            #c_c_t[clsid] = {}
            reqd = {'depart_id': clsid, 'term_id': termid}
            with capp_smsg('get_selectSheSchedule') as qer:
                realurl = self.handle_msger(reqs=reqd)
                srt = qer.get(urlpath=realurl)
            if srt['code'] != 0 or 'data' not in srt:
                continue
            for cinfo in srt['data']:
                if cinfo['teacherid']:
                    # counld be ""
                    if cinfo['course_id'] not in c_c_t[clsid]:
                        c_c_t[clsid][cinfo['course_id']] = dict(teacherid=cinfo['teacherid'], teachername=teachers[cinfo['teacherid']])
            time.sleep(0.1)
        return c_c_t

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