import logging
from modules import sysconsts, user_tbl
from assists import code_gender
from sys_config import cur_config

loger = logging.getLogger()

# 用户/组织管理类
# 主要用户独立系统-组织实体
# 
class admin(object):
	ORG_REGED = 1
	ORG_UNREGED = 0
	# 组织类型
	ORG_SUBTYPE_SCHOOL = "school"
	ORG_SUBTYPE_ORGANIZE = "organize"

	def __init__(self, session=None):
		self.session = session
		# extdata: store extend data if require
		# except_info: store exception infomations
		self.extdata = None
		self.except_info = None
		self.emsg = ""

	def handle_organization(self, action, idx=None, **kwargs):
		# @action:
		# list/new/delete/close
		# kwargs{new: objid(auto-gen)}
		# 兼容起见：schools类型作为organization通用类型名
		if action == 'list':
			return sysconsts('schools').simplelist(filterstr="status>=0")
		elif action == 'new':
			org_name = kwargs["title"]
			org_type = kwargs.get("subtype", "organize")
			remark = kwargs.get("extdata", "")
			objid = kwargs.get("objid") or code_gender(only_char=True)
			return sysconsts('schools').newitem(objid, title=org_name, subtype=org_type, value_int=self.__class__.ORG_REGED, extdata=remark)
		elif action == 'close':
			return sysconsts('shcools').set_valueint(idx, VINT_UNREGED)
		elif action == 'delete':
			return sysconsts('schools').delitem(idx)
		elif action == 'modify':
			return sysconsts('schools').moditem(idx, **kwargs)

	def handle_users(self, action, idx=None, byobj=False, **kwargs):
		'''
		@action:
		list/add/delete/import
		@ byobj: handle by organization(objectid)-all-users
		@kwargs: {
			add: dbm_user_require: userid,wxuserid,objid // 独立系统，无需wxuserid，统一置"";userid: 用户账号，自定义
			import: xls_file_path: string
		}
		'''
		objid = kwargs['objid']
		if action == 'list':
			page = int(kwargs.get('page', 1))
			size = int(kwargs.get('page_limit', 50))
			if page == 1:
				total = user_tbl._count()
				if total == 0:
					self.extdata = 0
					return []
			return user_tbl.list_users(objid=objid, page=page, size=size)
		elif action == 'add':
			# manual addition:
			pass
		elif action == 'import':
			pass
		elif action == 'delete':
			pass
		else:
			return False