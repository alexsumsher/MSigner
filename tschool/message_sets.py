#!/usr/bin/env python
# -*- coding: utf8
# 
# get mode.
# mapname: (sub_url_path, keys, return_keys_of_string_array)
appmsg_sets = {
    'get_schoolinfo': ("/api/open/getObjectInfo", (), "name,logo,edu_type"),
    'get_userinfo': ("/api/open/getUserInfo", ("userid",), "name,head,departid,wxuserid,wxdepartid,other_departid,other_wxdepartid,is_subscribe,user_no,ic_card_id,cellphone,type,gender,duty,teach_title,join_date"),
    'get_admininfo': ("/api/open/getAdminInfo", ("userid"), "id,name,is_supper"),
    'get_school': ('/api/open/getObjectInfo', (), 'name,logo,edu_type'),
    'get_dptinfobyId': ('/api/open/getDepartInfoById', ('departid',), 'level,parentid,wxdepartid,type,departname,departcode,join_year'),
    'get_users': ('/api/common/searchUser', ('usertype', 'departid', 'level', 'key', 'page', 'pageSize'), ''),
    'get_dpinfos': ('/api/open/getDepartmentInfoList', ('usertype',), ''),
    'get_workattendwaylist': ('/api/open/workAttendWayList', ('page', 'size'), ''),
    'get_teacherclass': ('/api/open/getManageDepartList', ('userid',), 'departid,departname,type'),
    'get_schoolyears': ('/api/schoolYear/getList', (), 'year_id,year_name,start_year,end_year'),
    'get_schoolterm': ('/api/schoolTerm/getList', (), 'term_id,term_name,start_term,end_term,year_id,year_name'),
    'get_courseinfo': ('/api/courseInfo/getList', (), 'course_id,course_title,course_code,course_hour,credit,color'),
    'get_teacherscheduel': ('/api/scheduleInfo/getListByUser', ('teacherid', 'term_id'), 'course_id,clsr_id,classid,week_type,curr_id,curr_lesson,curr_week,start_week,end_week'),
    'get_selectSheSchedule': ('/api/scheduleInfo/selectSheSchedule', ('depart_id', 'term_id'), 'week_type,course_id,curr_id,curr_week,curr_lesson,teacherid,clsr_id,start_week,end_week')
}

# post mode.
# mapname: (sub_url_path, post_body_keys, post_body_struct_name)
appmsg_sets2 = {
    'post_msg': ('/api/open/sendMsg', ('msgtype', 'wxuserid', 'wxdepartid', 'content'), 'data'),
    'updateStudent': ('/api/userInfo/updateStudent', ('msgtype', 'wxuserid', 'wxdepartid', 'content'), 'data'),
    'post_addstudent': ('/api/WorkAttendInfo/workAttend', ('userid', 'name', 'user_no', 'ic_card_id', 'departmentinfo[0][departid]', 'join_date', 'cellphone', 'gender'), 'StudentInfo')
}
