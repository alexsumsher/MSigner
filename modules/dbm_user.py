#!/usr/bin/env python
# -*- coding: utf8
from datetime import datetime as DT
import logging

from libs import simple_tbl


loger = logging.getLogger()

class user_tbl(simple_tbl):
	work_table = 'users'
	main_keys = ('uid', 'userid', 'wxuserid', 'openid', 'objid', 'departid', 'username', 'wxname', 'password', 'phonenumber', 'regdtime', 'status')
	list_keys = 'uid,userid,wxuserid,openid,departid,username,regdtime,status'
	require_keys = 'userid,wxuserid,objid'
	def_v = {'phonenumber': '', 'status': 0, 'password': '123456'}
	pkey = 'uid'

	STA_UNREG = 0 # 已入库，未注册
	STA_NORMAL = 1
	STA_BANNED = -1

	create_syntax = """CREATE TABLE `{tbl_name}` (\
	`uid` INT NOT NULL AUTO_INCREMENT, \
	`userid` VARCHAR(28) NOT NULL,\
	`wxuserid` VARCHAR(28) NOT NULL,\
	`openid` VARCHAR(32) DEFAULT NULL,\
	`objid` VARCHAR(28) DEFAULT NULL,\
	`departid` VARCHAR(28) DEFAULT NULL,\
	`username` VARCHAR(16) DEFAULT NULL,\
	`wxname` VARCHAR(16) DEFAULT NULL,\
	`password` VARCHAR(16) NOT NULL,\
	`phonenumber` VARCHAR(11),\
	`regdtime` DATETIME,\
	`status` TINYINT DEFAULT 0,\
	PRIMARY KEY (`uid`),\
	UNIQUE KEY `_userid` (`userid`),\
	KEY `_openid` (`openid`)\
	)ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8mb4;
	"""
	# uid: 序号
	# userid,username: 来源于智慧校园平台数据
	# openid: 从微信访问注册时的识别名
	
	@classmethod
	def reg_new(cls, userid, objid, username, wxname="", phonenumber="", regdtime=None):
		form = dict(userid=userid, objid=objid, username=username, wxname=wxname, phonenumber=phonenumber, regdtime=regdtime or DT.today())
		return cls._manage_item('new', orign_data=form)

	@classmethod
	def regist(cls, userid, objectid, others=None):
		# 用户注册：
		# 用户注册过程：
		# 1. 先由管理员导入账号，包含userid、wxuserid两个量，并隐式包含objid（组织编号）；导入后产生uid
		# 2. 用户在微信端登录，需要注册（匹配），此时需要用户提供独有的编号以匹配，由于不能导入用户的关键信息进行自动匹配，必须在第一步提供，uid/userid/wxuserid，由注册者手动输入验证
		# 3. 验证后填入openid，对于用户openid用户表示注册成功；
		# 3. 用户在H5页面登录，则自带userid，可自行匹配；
		if 'openid' not in others:
			raise ValueError("openid requrie!")
		if 'status' in others:
			others.pop('status')
		#set_str = cls.filter_dict(others, mode='pstr', exists_only=True, defv=cls.def_v)
		set_str = 'openid="%s",password="%s",regdtime="%s"' % (others['openid'], others['password'], DT.now())
		sqlcmd = 'UPDATE %s SET %s,status=%d WHERE objid="%s" AND userid="%s"' % (cls.work_table, set_str, cls.STA_NORMAL, objectid, userid)
		# return uid
		return cls._con_pool.execute_db(sqlcmd)

	@classmethod
	def ban_user(cls, uid, unban=False):
		if unban:
			return cls._single_mod(uid, 'status', cls.STA_NORMAL)
		return cls._single_mod(uid, 'status', cls.STA_BANNED)

	@classmethod
	def del_user(cls, uid):
		return cls._manage_item("delete", uid=uid)

	@classmethod
	def get_userby(cls, value, keyname=None, fullinfo=False):
		if keyname is None:
			if value.isdigit():
				keyname = 'phonenumber'
			elif len(value) < 5:
				keyname = 'username'
			elif len(value) <= 18:
				keyname = 'userid'
			else:
				keyname = 'openid'
		if fullinfo:
			columns = ','.join(cls.main_keys)
		else:
			columns = 'userid,objid'
		sqlcmd = 'SELECT %s FROM %s WHERE %s="%s"' % (columns, cls.work_table, keyname, value)
		dbrt = cls._con_pool.query_db(sqlcmd, one=True)
		if dbrt and fullinfo:
			return dict(zip(cls.main_keys, dbrt))
		return dbrt

	@classmethod
	def user_by_openid(cls, openid):
		sqlcmd = 'SELECT userid FROM %s WHERE openid="%s"' % (cls.work_table, openid)
		dbrt = cls._con_pool.query_db(sqlcmd, one=True)
		if dbrt:
			return dbrt[0]

	@classmethod
	def user_by_openid2(cls, openid):
		sqlcmd = 'SELECT userid,objid FROM %s WHERE openid="%s"' % (cls.work_table, openid)
		return cls._con_pool.query_db(sqlcmd, one=True)

	@classmethod
	def user_by_userid(cls, userid):
		udata = cls._vget(userid, "uid,wxuserid,openid,departid,username,password,regdtime,status", key_col="userid", cols=8)
		if udata:
			return {
			'uid': udata[0],
			'wxuserid': udata[1],
			'openid': udata[2],
			'departid': udata[3],
			'username': udata[4],
			'password': udata[5],
			'regdtime': udata[6],
			'status': udata[7],
			}

	@classmethod
	def list_users(cls, objid=None, page=1, size=50, with_banned=False, only_reged=False, by_dpid=None):
		f_list = []
		if objid:
			f_list.append('objid="%s"' % objid)
		if by_dpid:
			# dpids: 'dpid1,dpid2,...' => '("dpid1", "dpid2")'
			f_list.append('departid in ("%s")' % by_dpid.replace(',', '","'))
		if with_banned:
			f_list.append('status>=%d' % cls.STA_UNREG)
		elif only_reged:
			f_list.append('status>=%d' % cls.STA_NORMAL)
		if f_list:
			fstr = ' AND '.join(f_list)
		else:
			fstr = None
		offset = (page - 1) * size
		return cls._list_items(filterstr=fstr, limit=size, offset=offset)

	@classmethod
	def count_users(cls, objid=None, with_banned=False):
		f_list = []
		if objid:
			f_list.append('objid="%s"' % objid)
		elif with_banned:
			f_list.append('status>=0')
		if f_list:
			fstr = ' AND '.join(f_list)
		else:
			fstr = None
		return cls._count(bystr=fstr)

	@classmethod
	def import_user(cls, objid, userdata):
		# userid
		if 'userid' not in userdata:
			return False
		userdata['objid'] = objid
		dbrt = cls._manage_item('new', orign_data=userdata)
			# exitst!
		if not dbrt:
			return cls._vget(userdata['userid'], 'uid', key_col="userid", cols=1)
		return dbrt

	@classmethod
	def import_multi(cls, users, objid, precheck=False):
		# 从智慧校园批量导入
		# 第三方独立应用不能获取user_no（教工号）以及cellphone，以及用户姓名（注：老师只返回姓氏；家长不返回姓名），因此不可能包含相应的内容
		# 因此批量导入只能导入userid,wxuserid(可能用于发消息)
		if precheck:
			user_set = ','.join(['"%s"' % _['userid'] for _ in users])
			check_cmd = 'SELECT count(*) FROM %s WHERE objid="%s" AND userid in (%s)' % (cls.work_table, objid, user_set)
			conflicts = cls._con_pool.query_db(check_cmd, one=True)
			if conflicts and conflicts[0] > 0:
				return False
		# 确认应该是初次导入(空)还是二次导入
		n = cls._count('objid="%s"' % objid)
		sep = False if n > 0 else True
		value_list = []
		for user in users:
			value_list.append(dict(userid=user['userid'], wxuserid=user['wxuserid'], objid=objid, username=user['username'], departid=user['departid'], phonenumber=user.get("cellphone", "")))
		print(value_list)
		return cls.huge_insert(value_list, autocolumn="userid,wxuserid,objid,username,departid,phonenumber", singlecmd=sep)

	@classmethod
	def uid2openid(cls, userids, autokick=True):
		if isinstance(userids, str):
			userids = '"' + userids.replace(',', '","') + '"' if userids.index(',') > 0 else userids
		else:
			userids = ','.join(['"%s"' % u for u in userids])
		sqlcmd = 'SELECT userid,openid FROM %s WHERE userid in (%s)' % (cls.work_table, userids)
		dbrt = cls._con_pool.query_db(sqlcmd)
		if autokick:
			export = []
			errors = []
			for g in dbrt:
				if g[1] is None:
					errors.append(g[0])
					continue
				export.append(g)
			if len(errors) > 0:
				loger.warning("USER2WXUSER: user: [%s] are not found!" % errors)
			return export
		return dbrt
