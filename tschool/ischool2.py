#!/usr/bin/env python
# -*- coding: utf8

"""
working wxcampus server
"""
import time

from libs import binfile
from tschool import appmsg_sets, appmsg_sets2, capp_smsg, thirdsvr2
from modules import sysconsts
from ultilities import dict_search2, dict_search3
from sys_config import cur_config, logging
#from cur_config_test import cur_config, logging
loger = logging.getLogger()


class myschool(thirdsvr2):
    token = cur_config.token()

    """myschool, comunicate with tencent smart school"""
    # seperator with mysql data table
    
    @classmethod
    def settoken(cls, token):
        if isinstance(token, dict):
            cls.token = token

    @classmethod
    def myschool(cls, name, tokens=None, **ext_token):
        if name in cls.SCHOOLS:
            return cls.SCHOOLS[name]
        elif tokens:
            _school = cls(tokens, **ext_token)
            return _school

    def __init__(self, school_objid, db_preifx=None, chkable=False):
        # student_department;
        # teacher_department;
        super(myschool, self).__init__(school_objid, db_preifx)
        if chkable:
            sinfo = self.schoolinfo()
            if sinfo['code'] != 0:
                raise ValueError("check school failure: %s" % sinfo['msg'])

    @property
    def objid(self):
        return self.token['school_objid']

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

    def _class_2_grade(self, classid):
        # 根据classid获取所在年级
        schooldata = self.col_departments(1)
        if not schooldata:
            return
        if isinstance(classid, dict):
            clsid = classid['departid']
            gid = clsid['parentid']
            grade = dict_search2(schooldata, 'departid', gid)
            return grade
        grades = dict_search2(schooldata, 'level', '5')
        if not grades:
            return None
        for g in grades:
            for c in g['child']:
                if c['departid'] == classid:
                        return g
        return None

    def _list_class(gradeid=""):
        # 列出年级下的班级
        schooldata = self.col_departments(1)
        if not schooldata:
            return
        if not gradeid:
            return dict_search2(schooldata, 'level', '6')
        grade = dict_search2(schooldata, 'departid', gradeid, one=True)
        return grade['child'] if isinstance(grade, dict) and 'child' in grade else None

    def _getclass_s(clsid_s, gradeid=None, take=None):
        # 在全校/gradeid年级搜索符合条件的班级dict: {class_dpid: {classdict}, ...}
        # take more then one class for a fasterway
        # clsid_s: [clsid, clsid, ...]
        # if gradeid: find in grade
        schooldata = self.col_departments(1)
        if not schooldata:
            return
        clslist = clsid_s if isinstance(clsid_s, (list, tuple)) else [_.strip() for _ in clsid_s.split(',')]
        source = dict_search2(schooldata, 'departid', gradeid, one=True) if gradeid else schooldata
        result = dict_search3(source, 'departid', clslist, listout=False, outkey='departid')
        if not take:
            return result
        out = {}
        for k,v in result.items():
            out[k] = v[take]
        return out

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

    def get_teacher_grades(self, userid, termid):
        # 学校/上级单位/合作伙伴用
        # 通过课表功能获取教师所教学的学科在各个年级的分布: 老师A-三年级语文+二年级体育
        # 输出CCT（Course-Class mapping of Teacher): {courseid1: [grade_dict1, grade_dict2, ...], courseid2: ...}
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
        # 学校/上级单位/合作伙伴用
        # 获取特定course的CCT映射 [course-class of <teacher>] (get_teacher_grades的部分)
        # return： {classid: {classdata}, ...}
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
            print("no teacher founld!")
            return None
        print(teachers)
        classes = self._list_class()
        print("classes count: %s" % len(classes))
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