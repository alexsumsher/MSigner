import logging
from .libs import Qer

loger = logging.getLogger()


class tree_table(Qer):

	"""
	构造支持Tree(json like)结构数据表；单表;用于存储多个tree
	treedata: data from database: ((...), (...), ...) or [{}, {}, ...]
	nodedata: data for json: {..., children: [{..., children: []...}, ...]}
	"""
	ALL_TREES = dict() # 'typename': top_nod_nid

	work_table = 'treedatas'
	pkey = 'nid'
	#main_keys = ('nid', 'title', 'value_int', 'value_str', 'parent', 'top_node', 'level', 'npath')
	main_keys = 'nid,title,value_int,value_str,parent,top_node,level,npath'
	create_syntax = """CREATE TABLE `{tbl_name}` (\
	`nid` INT NOT NULL AUTO_INCREMENT,\
	`title` VARCHAR(32) NOT NULL,\
	`value_int` INT DEFAULT 0,\
	`value_str` VARCHAR(64),\
	`parent` INT NOT NULL,\
	`top_node` INT NOT NULL,\
	`level` TINYINT DEFAULT 1,\
	`npath` VARCHAR(128) NOT NULL,\
	PRIMARY KEY (`nid`),\
	KEY `_title` (`title`),\
	) ENGINE=InnoDB CHARSET=utf8mb4;"""

    @classmethod
    def create_table(cls, tablename="", force=False):
        if not cls.create_syntax:
            raise ValueError("NO CREATE SYNTAX!")
        if tablename:
            cls.work_table = tablename
        else:
            tablename = cls.work_table
        if not tablename:
            raise ValueError("no table name!")
        if force:
            cls._con_pool.execute_db("DROP TABLE %s" % tablename)
        return cls._con_pool.execute_db(cls.create_syntax.format(tbl_name=tablename))

	@staticmethod
	def _path(pathstr):
		return [int(_) for _ in pathstr.split(',')]

	@staticmethod
	def _node2str(node, mode=0, vtype="str", **treedata):
		# 建立有效数据部分的SQL插入字符串
		# 如果vtype == str, 则默认value则映射到value_str字段
		if vtype == "str":
			v_str = node.get("value_str") or node.get("value", "")
			v_int = 0
		elif vtype == "int":
			v_int = int(node.get('value_int') or node.get("value", 0))
			v_str = ""
		elif vtype == "both":
			v_str = node.get("value_str") or node.get("value", "")
			v_int = int(node.get("value_int"), 0)
		else:
			v_str = ""
			v_int = 0
		if mode == 0:
			# insert
			out = '"%s",%d,"%s"' % (node['title'], v_int, v_str)
		elif mode == 1:
			# update
			out = 'title="%s",value_int=%d,value_str="%s"' % (node['title'], v_int, v_str)
		if treedata:
			if mode == 0:
				out += ',%d,%d,%d,"%s"' % (treedata['parent'], treedata['top_node'], treedata['level'], treedata['npath'])
			elif mode == 1:
				out += ',parent=%d,top_node=%d,level=%d,npath="%s"' % \
				(treedata['parent'], treedata['top_node'], treedata['level'], treedata['npath'])
		return out

	@staticmethod
	def _tree2nodes(subtree, vtype="str", use_value=True):
		# subtree(whole sub tree):
		# {title, value_int, value_str, children:[]}
		# children: [{title, value_int, value_str, children:[], {title, value_int, value_str, children: None}}]
		allnodes = []
		pnode = []
		childrens = []
		childrens.append(subtree.pop('children'))
		pnode.append(subtree['title'])
		subtree['parent'] = 0
		subtree['top_node'] = 0
		subtree['level'] = 1
		subtree['npath'] = ""
		if use_value:
			if vtype == 'int':
				subtree['value'] = subtree.pop("value_int")
				subtree.pop("value_str")
			else:
				subtree['value'] = subtree.pop("value_str")
				subtree.pop("value_int")
		allnodes.append(subtree)
		while len(childrens)>0:
			_p = pnode.pop(0)
			for n in childrens.pop(0):
				_c = n.pop('children')
				if _c:
					childrens.append(_c)
					pnode.append(n['title'])
				if use_value:
					if vtype == 'int':
						_n = dict(title=n['title'], value=int(n['value_int'] or 0), parent=_p)
					else:
						_n = dict(title=n['title'], value=n['value_str'], parent=_p)
				else:
					_n = dict(title=n['title'], value_int=int(n.get('value_int', 0)), value_str=n.get('value_str', ""), parent=_p)
				allnodes.append(_n)
		return allnodes

	@classmethod
	def new_top(cls, node, vtype="str"):
		node_str = cls._node2str(node)
		sqlcmd = 'INSERT INTO %s(title,value_int,value_str,parent,top_node,level,npath) VALUES(%s,0,0,1,"")' \
		% (cls.work_table, node_str)
		dbrt = cls._con_pool.execute_db(sqlcmd, get_ins_id=True)
		if dbrt:
			cls.ALL_TREES[node['title']] = dbrt
		return dbrt

	@classmethod
	def new_tree(cls, subtree, vtype="str"):
		# with write into db: Create a Tree into DB from JSON_DATA:
		# @subtree: {title, value_int, value_str, children:[]}
		# @vtype(value_type): str | int | both | None/""/0
		# return: list of nodes
		def json2node(jdata, vt=vtype):
			D = dict(title=jdata['title'])
			if vt == "str":
				D['value_str'] = jdata.get('value_str') or jdata.get("value", "")
				D['value_int'] = 0
			elif vt == 'int':
				D['value_int'] = int(jdata.get("value_int") or jdata.get("value", 0))
				D['value_str'] = ""
			elif vt == 'both':
				D['value_str'] = jdata.get('value_str') or jdata.get("value", "")
				D['value_int'] = int(jdata.get("value_int"), 0)
			else:
				D['value_str'] = ""
				D['value_int'] = 0
			return D

		allnodes = []
		parent_info = []
		childrens = []
		childrens.append(subtree.pop('children'))
		subtree['parent'] = 0
		subtree['top_node'] = 0
		subtree['level'] = 1
		subtree['npath'] = ""
		topid = cls.new_top(subtree, vtype=vtype)
		if not topid:
			raise RuntimeError("not able to create tree!")
		subtree['nid'] = topid
		parent_info.append({'title': subtree['title'], 'level': 1, 'nid': topid, 'npath': ''})
		allnodes.append(subtree)
		while len(childrens)>0:
			_p = parent_info.pop(0)
			for n in childrens.pop(0):
				_c = n.pop('children')
				_n = json2node(n)
				_n['parent'] = _p['nid']
				_n['top_node'] = topid
				_n['level'] = _p['level'] + 1
				_n['npath'] = _p['npath'] + ',' + str(_p['nid']) if _n['level'] > 2 else str(_p['nid'])
				_nid = cls.append_to(_p['nid'], _n)
				_n['nid'] = _nid
				if _nid:
					allnodes.append(_n)
					if _c:
						childrens.append(_c)
						parent_info.append({'title': _n['title'], 'level': _n['level'], 'nid': _nid, 'npath': _n['npath']})
		return allnodes

	@classmethod
	def flush_tree(cls, subtree):
		pass

	def __new__(cls, typename, vint=0, vstr=""):
		if typename in cls.ALL_TREES:
			return super(tree_table, cls).__new__(cls)
		sqlcmd = 'SELECT nid FROM %s WHERE title="%s" AND level=1' % (self.__class__.work_table, typename)
		dbrt = cls._con_pool.query_db(sqlcmd, one=True)
		if dbrt:
			cls.ALL_TREES['typename'] = dbrt
			return super(tree_table, cls).__new__(cls)
		# create type
		ccmd = 'INSERT INTO %s(title,value_int,value_str,parent,top_node,level,npath) VALUES("%s",%d,"%s",0,0,1,"")' % \
		(cls.work_table, typename, vint, vstr)
		nid = cls._con_pool.execute_db(ccmd)
		if nid:
			cls.ALL_TREES['typename'] = nid
			return super(tree_table, cls).__new__(cls)
		raise ValueError("Can not Create type-node for type: %s" % typename)

	def __init__(self, typename, vtype="str", use_value=True):
		# 新的类型[Tree]
		# @typename: 新的树类型，等同于top_node的title
		# @use_value: 输入/输出采用value字段替代(value_str或value_int)，视vtype决定
		self.typename = typename
		self.topnid = self.__class__.ALL_TREES[typename]
		self.con = self.__class__._con_pool
		self.vtype = vtype
		self.use_value = use_value

	def _node2dict(self, nodedata, full=False):
		# create node-dict from nodedata from db like: (nid,title,value_int,value_str, {parent,top_node,level,npath if full})
		# @full: with tree_infos
		# @use_value: dict's value data by keyname: value(not value_int/value_str, which specified by self.vtype)
		if full and len(nodedata) != 8:
			raise ValueError("Not Enough Data from nodedata while fulldata is specified!")
		if full:
			D = dict(nid=nodedata[0], title=nodedata[1], parent=nodedata[4], top_node=nodedata[5], level=nodedata[6], npath=nodedata[7])
		else:
			D = dict(nid=nodedata[0], title=nodedata[1])
		if self.use_value:
			D['value'] = nodedata[2] if self.vtype == "int" else nodedata[3]
		else:
			D['value_int'] = nodedata[2]
			D['value_str'] = nodedata[3]
		return D

	def value_search(self, vstr="", vint=0, with_children=False):
		# search node by title under a self.topnid[tree]
		# auto recognize: value_int/value_str
		if self.vtype == "both":
			search_cmd = 'SELECT nid FROM {} WHERE top_node={} AND value_int={} AND value_str="{}"'.format(self.work_table, self.topnid, vint, vstr)
		elif self.vtype == 'int':
			search_cmd = 'SELECT nid FROM {} WHERE top_node={} AND value_int={}'.format(self.work_table, self.topnid, vint)
		elif self.vtype == 'str':
			search_cmd = 'SELECT nid FROM {} WHERE top_node={} AND value_str="{}"'.format(self.work_table, self.topnid, vstr)
		dbrt = self.con.query_db(search_cmd, one=True)
		# if multi match, take the closest
		if not dbrt:
			return
		return self.con.get_node(dbrt[0], with_children=with_children)

	def get_node(self, nid, with_children=True):
		# export:
		# {title, value_int, value_str, children:}
		# thisnode = (1,'a',0,'',0,0,1,'');
		# allnodes=((2,'aa1',0,'',1,1,2,'1'),(3,'aa2',0,'',1,1,2,'1'),(4,'aaa1',0,'',3,1,3,'1,3'),(5,'aaa2',0,'',3,1,3,'1,3'),(6,'aaa3',0,'',2,1,3,'1,2'),(7,'aaaa1',0,'',6,1,4,'1,2,6'))
		# {'nid': 1, 'title': 'a', 'value_int': 0, 'value_str': '', 'children': [{'nid': 2, 'title': 'aa1', 'values_int': 0, 'value_str': '', 'children': [{'nid': 6, 'title': 'aaa3', 'values_int': 0, 'value_str': '', 'children': [{'nid': 7, 'title': 'aaaa1', 'values_int': 0, 'value_str': '', 'children': None}]}]}, {'nid': 3, 'title': 'aa2', 'values_int': 0, 'value_str': '', 'children': [{'nid': 4, 'title':'aaa1', 'values_int': 0, 'value_str': '', 'children': None}, {'nid': 5, 'title': 'aaa2', 'values_int': 0, 'value_str': '', 'children': None}]}]}
		try:
			thisnode = self.con.query_db("SELECT %s FROM %s WHERE nid=%d" % (self.main_keys, self.work_table, nid), one=True)
			export = self._node2dict(thisnode)
		except (ValueError, IndexError, TypeError):
			loger.error("Not able to get node with nid: %d" % nid)
			return False
		#export = {'nid': thisnode[0], 'title': thisnode[1], 'value_int': thisnode[2], 'value_str': thisnode[3]}
		if not with_children:
			return export
		export['children'] = None
		allnodes = self.con.query_db('SELECT %s FROM %s WHERE topid=%d AND level>%d AND FIND_IN_SET("%s", npath) ORDER BY level' % \
			(self.main_keys, self.work_table, self.topnid, thisnode[6], nid))
		if not allnodes:
			return export
		export['children'] = []
		lvnodes = [export] # all node on current level
		nlvnodes = [] # nodes on next level
		lv0 = thisnode[6] + 1 # thisnode level+1 as the start level of sub nodes
		for n in allnodes:
			#_nid = n[0]
			#_title = n[1]
			#_v_int = n[2]
			#_v_str = n[3]
			_parent = n[4]
			_lv = n[6]
			_d = self._node2dict(n)
			_d['children'] = None
			#_d = {'nid': _nid, 'title': _title, 'values_int': _v_int, 'value_str': _v_str, 'children': None}
			if _lv == lv0:
				for i in range(len(lvnodes)):
					n = lvnodes[i]
					if n['nid'] == _parent:
						if n['children'] is None:
							n['children'] = [_d]
						else:
							n['children'].append(_d)
						nlvnodes.append(_d)
						break
				continue
			# from upper level to nextlevel, cur_childrens is the list of upper nodes
			lvnodes.clear()
			lvnodes,nlvnodes = nlvnodes,lvnodes
			lv0 = _lv
		return export

	def title_search(self, title, with_children=True, strict=False):
		# search node by title under a self.topnid[tree]
		if strict:
			search_cmd = 'SELECT nid,title FROM {} WHERE top_node={} AND title="{}"'.format(self.work_table, self.topnid, title)
		else:
			search_cmd = 'SELECT nid,title FROM {} WHERE top_node={} AND title like "%{}%"'.format(self.work_table, self.topnid, title)
		dbrt = self.con.query_db(search_cmd)
		# if multi match, take the closest
		if not dbrt:
			return
		if len(dbrt) > 1:
			# shortest is the best
			target_idx = 0
			xlen = 999
			c = 0
			for row in dbrt:
				_len = len(row[1])
				if _len < xlen:
					xlen = _len
					target_idx = c
				c += 1
			target = dbrt[target_idx]
		else:
			target = dbrt[0]
		return self.get_node(target[0], with_children=with_children)

	def append_to(self, parentid=0, node):
		parentid = parentid or self.topnid
		dbrt = self.con.query_db("SELECT nid,parent,top_node,level,npath FROM %s WHERE nid=%d" % (self.work_table, parentid), one=True)
		if not dbrt:
			raise ValueError("parent not found!")
		pnode = dbrt[0]
		_npath = pnode[4] + ',' + str(_parent)
		node_str = self._node2str(node, mode=1, parent=pnode[0], top_node=pnode[2], level=pnode[3]+1, npath=_npath)
		sqlcmd = 'INSERT INTO %s(title,value_int,value_str,parent,top_node,level,npath) VALUES(%s, %s)' % (cls.work_table, node_str)
		nid = self.con.execute_db(sqlcmd, get_ins_id=True)
		return nid

	def move_node(self, nid, new_parent, with_children=True):
		# if not with_children, childrens should attach to parent node
		# if top, remove whole tree;
		try:
			thisnode = self.con.query_db("SELECT nid,parent,top_node,level,npath FROM %s WHERE nid=%d" % (self.work_table, nid), one=True)
			pnode = self.con.query_db("SELECT nid,parent,top_node,level,npath FROM %s WHERE nid=%d" % (self.work_table, new_parent), one=True)
		except (ValueError,IndexError):
			return False
		if thisnode[6] == 1:
			return False
		if thisnode[2] != pnode[2]:
			loger.error("not allow to move to other tree!")
			return False
		new_path = pnode[-1] + ',' + str(pnode[0])
		old_path = thisnode[-1] + ',' + str(thisnode[0])
		sqlcmd = 'UPDATE %s SET parent=%d,npath="%s" WHERE nid=%d' % (self.work_table, new_parent, new_path, nid)
		if with_children:
			sqlcmd += 'UPDATE %s SET npath=REPLACE(npath, "%s", "%s") WHERE nid>0 AND top_node=%d AND FIND_IN_SET("%s", npath)' \
			% (self.work_table, old_path, new_path, thisnode[2], nid)
		else:
			sqlcmd += 'UPDATE %s SET parent=%d WHERE parent=%d' % (self.work_table, thisnode[1], nid)
			sqlcmd += ';UPDATE %s SET npath=REPLACE(npath, ",%d,", ",%d,") WHERE nid>0 AND top_node=%d AND FIND_IN_SET("%s",npath)' \
			% (self.work_table, nid, thisnode[1], thisnode[2], nid)
		return self.con.do_sequence(sqlcmd)

	def remove_node(self, nid, with_children=True):
		try:
			thisnode = self.con.query_db("SELECT nid,parent,top_node,level,npath FROM %s WHERE nid=%d" % (self.work_table, nid), one=True)
		except (ValueError, IndexError):
			return False
		if thisnode['level'] == 1:
			# remove tree
			sqlcmd = 'DELETE FROM %s WHERE nid>0 AND top_node=%d' % (self.work_table, nid)
			return self.con.execute_db(sqlcmd)
		if with_children:
			sqlcmd = 'DELETE FROM %s WHERE nid>0 AND top_node=%d AND FIND_IN_SET("%s",npath)' \
			% (self.work_table, thisnode[2], nid)
		else:
			new_path = thisnode[-1]
			sqlcmd = 'UPDATE %s SET parent=%d WHERE parent=%d' % (self.work_table, thisnode[1], nid)
			sqlcmd += ';UPDATE %s SET npath=REPLACE(npath, ",%d,", ",%d,") WHERE nid>0 AND top_node=%d AND FIND_IN_SET("%s",npath)' \
			% (self.work_table, nid, thisnode[1], thisnode[2], nid)
		sqlcmd += ';DELETE FROM %s WHERE nid=%d' % (self.work_table, nid)
		return self.con.do_sequence(sqlcmd)


if __name__ == '__main__':
	tns = {'title': 'a', 'children':[{'title': 'aa1', 'children': None},{'title':'aa2', 'children':[{'title': 'aaa1', 'children':None},{'title': 'aaa2', 'children':None}]}]}
	cls.new_tree(tns)