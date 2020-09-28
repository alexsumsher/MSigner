import datetime
from modules import sysconsts



def on_school(action, *args, **kwargs):
	"""
	quick data operation:
	school:
	key: objid
	title: school_name
	status: 0-normal
	"""
	VINT_REGED = 1
	VINT_UNREGED = 0
	if action == 'get':
		return sysconsts('schools').data(key=args[0])
	elif action == 'list':
		return sysconsts('schools').simplelist(filterstr="status>=0")
	elif action == 'keyid-set':
		pass
	elif action == 'keyid-get':
		# value_int: keyId, value: key(授权密钥)
		rt = sysconsts('keyid').value(key=args[0], target=0b11)
		return rt
	elif action == 'add':
		# add new one as registed
		# value_int
		objid = kwargs['objectid']
		schoolname = kwargs['schoolname']
		return sysconsts('schools').newitem(objid, title=schoolname, value_int=VINT_REGED)
		# idx,key,title,value,value_int
	elif action == 'unreg':
		sid = args[0]
		return sysconsts('shcools').set_valueint(sid, VINT_UNREGED)
	elif action == 'set_idtime':
		# 更新导入全校教师的时间，二次导入时，joindate>import_date的才有必要增加
		objid = kwargs['objectid']
		dtime = kwargs.get('dtime') or datetime.datetime.now()
		return sysconsts('user_import_dtime').setitem(objid, dtime)
	elif action == 'get_idtime':
		pass
	return None