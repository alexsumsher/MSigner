import logging
from modules import sysconsts, user_tbl
from assists import code_gender
from sys_config import cur_config

loger = logging.getLogger()


class data_handler(object):

	def __init__(self):
		self.extvalue = None
		self.extdata = None
		self.emsg = ""

	def list_schools(self, as_opts=False):
		# @as_opts: {value, title}
		if as_opts:
			dbrt = sysconsts('schools').simplelist(filterstr="status>=0")
			rt = []
			for v in dbrt:
				rt.append({'value': v['ikey'], 'title': v['title']})
			return rt
		else:
			return sysconsts('schools').simplelist(quick=False, filterstr="status>=0")
