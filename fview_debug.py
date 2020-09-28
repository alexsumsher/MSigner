#!/usr/bin/env python
# -*- coding: utf8
from flask import Flask, request, json, send_file
from tschool import myschool, pmsgr, capp_smsg, appmsg_sets, appmsg_sets2

def debuging():
    objid = request.args.get('objectid', "2XaxJgvRj6Udone")
    ischool = myschool.myschool(objid)
    if request.method == 'GET':
        rtdata = {'respon': 'failure'}
        testtype = request.args.get('testtype')
        action = request.args.get('action')
        if testtype:
            reqer = appmsg_sets.get(testtype) or appmsg_sets2.get(testtype)
            if reqer:
                rtdata = {'reqtype': testtype, 'requrl': reqer[0], 'reqkeys': ','.join(reqer[1])}
        elif action == 'alltypes':
            alltypes = list(appmsg_sets.keys())
            alltypes.extend(appmsg_sets2.keys())
            types = ','.join(alltypes)
            rtdata = {'respon': 'success', 'types': types}
        elif action == 'listusers':
            reqd = dict()
            reqd['usertype'] = request.args.get('usertype')
            reqd['departid'] = request.args.get('departid')
            reqd['level'] = request.args.get('level')
            reqd['page'] = request.args.get('page', 1)
            reqd['pageSize'] = request.args.get('page_limit', 20)
            realurl = ischool.handle_msger(reqs=reqd)
            with capp_smsg('get_users') as qer:
                wx_rtdata = qer.get(urlpath=realurl)
            return json.dumps(wx_rtdata)
        elif action == 'get_teacher':
            uid = request.args.get('userid')
            teacher = worktbl.d_get('teachers', uid)
            if teacher:
                rtdata['data'] = teacher
            else:
                rtdata['respon'] = 'failure'
        else:
            return send_file('statics/htmls/debug.html', mimetype='text/html')
        return json.dumps(rtdata)
    requrl = request.args.get('requrl')
    reqname = request.args.get('reqname')
    wx_rtdata = None
    reqd = request.form.to_dict() or {}
    with capp_smsg(reqname, postdata=reqd) as qer:
        if reqname.startswith('post'):
            reqbox = dict()
            reqbox[appmsg_sets2[reqname][2]] = reqd
            realurl = ischool.handle_msger(postdata=reqbox)
            wx_rtdata = qer.post(posturl=realurl)
        else:
            realurl = ischool.handle_msger(reqs=reqd)
            #realurl = realurl.encode('utf8') if isinstance(realurl, unicode) else realurl.decode('gbk').encode('utf8')
            wx_rtdata = qer.get(urlpath=realurl)
    return json.dumps(wx_rtdata or {'code': 0, 'respon': 'failure'})