#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import re
from datetime import datetime as DT, timedelta as TD

#   select * from work_rec_ym Y left join (select eid,sum(contracts) as cons,sum(invitation) as invs from work_rec_d where eid=21 and todate like "2017-06%") D on Y.eid=D.eid where Y.code_year=2017 and Y.code_month=6
#   select * from ((select eid,m_contracts,m_invitation from work_rec_ym where code_year=2017 and code_month=6) Y left join (select eid,sum(contracts) as cons,sum(invitation) as invs from work_rec_d where eid=21 and todate like "2017-06%") D on Y.eid=D.eid)
#   

class emptyCon(object):

    def __init__(self):
        self.w = 'pool'

    def us_execute_db(self, sql):
        print(sql)
        return True

    def execute_db(self, sql, get_ins_id=False):
        print(sql, get_ins_id)
        return 1

    def query_db(self, sql, one=False, rt=None):
        print(sql)
        return rt

    def do_sequence(self, sql, rt=None):
        print(sql)
        return rt

#
class Qer(object):
    query_limit = 50
    _con_pool = None

    @classmethod
    def set_con_pool(cls, con_pool):
        if hasattr(con_pool, 'w') and con_pool.w == 'pool':
            # in order to avoid that we may forget to write 'self.con=self.__class__._con_pool', then system will auto reference self.con to self.__class__.con
            cls.con = cls._con_pool = con_pool
        else:
            raise ValueError('NOT A CON-POOL!')

    # if set the _con_pool for Qer, then if there was not set con_pool for subclass, witch will point to Qer's
    # for common usage, DON'T use __con_pool which will not be referenced by subclass!
    # if new instance with a con key_value, then set the class con_pool to it
    def __new__(cls, *args, **kwargs):
        if 'con' in kwargs and hasattr(kwargs['con'], 'w') and kwargs['con'].w == 'pool':
            cls.con = cls._con_pool = kwargs['con']
        return super(Qer, cls).__new__(cls)

    # a) class new_qer_1(Qer), ins_of_new_qer_1() => ins_of_new_qer_1/new_qer_1 ._con_pool == Qer._con_pool
    # b) class new_qer_2(Qer), ins_of_new_qer_2(con=new_con_pool) => ins_of_new_qer_2/new_qer_2 ._con_pool == new_con_pool
    # remark: __init__ with self.con = self.__class__._con_pool for quick using con
    def __init__(self, con=None):
        # if con is not a pool, means this con is normal db connection and only work for this instance!
        if con and hasattr(con, 'w') and con.w == 'pool':
            self.con = self.__class__._con_pool
        else:
            self.con = con

    @staticmethod
    def str_list(strin, isint=False, spliter=","):
        if isinstance(strin, (list, tuple)):
            if isint and isinstance(strin[0], str):
                return [int(_) for _ in strin]
            return strin
        elif not isinstance(strin, str):
            raise ValueError("require list or tuple or str!")
        if spliter is None:
            # any spliter... but only works with integer-list or asciichar(plus'_'symbal)-list
            if isint:
                return [int(_) for _ in re.split('[^0-9]+', strin)]
            else:
                return re.split(r'[^\w_]+', strin)
        # if spliter is space, no strip
        if spliter == ' ':
            return [int(_) for _ in strin.split(spliter)] if isint else strin.split(spliter)
        _strin = strin.replace(' ', '')
        if isint:
            return [int(_) for _ in _strin.split(spliter)]
        return _strin.split(spliter)

    @classmethod
    def filter_dict(cls, origin_data, colns=None, require_keys=None, exists_only=False, defv=None, mode='dict', parentheses=False):
        # check a input dict/request.args&form for required keys, and covert to string/dict.
        # string "NULL" as default value replace [None]
        # update with require_keys: onlyexists is banned
        defv = defv or cls.def_v or {}
        outs = dict()
        require_keys = require_keys or cls.require_keys
        if exists_only or require_keys is None:
            require_keys = []
        else:
            require_keys = cls.str_list(require_keys)
        # usually we pass main_keys[1:] in as colns
        #colns = colns if isinstance(colns, (list, tuple)) else colns.split(',') if isinstance(colns, str) else origin_data.keys()
        #colns = origin_data.keys() if colns is None else Qer.str_list(colns)
        colns = cls.str_list(colns or cls.main_keys[1:] or origin_data.keys())
        real_colns = []
        for _ in colns:
            v = origin_data.get(_)
            if v is None:
                if exists_only:
                    continue
                if _ in require_keys and _ not in defv:
                    raise ValueError("require key<%s> is not given!" % _)
                else:
                    v = defv.get(_)
                if v is None:
                    continue
            real_colns.append(_)
            if isinstance(v, str):
                if re.fullmatch(r'\d+(\.\d+)?', v):
                    outs[_] = v
                else:
                    outs[_] = '"' + str(v) + '"'
            elif isinstance(v, (int, float)) or v == "NULL":
                outs[_] = str(v)
            else:
                outs[_] = '"' + str(v) + '"'
        if mode == 'dict':
            return outs
        elif mode == 'pstr':
            vstr = ''
            for _ in real_colns:
                vstr += '%s=%s,' % (_, outs[_])
            return vstr[:-1]
        elif mode == 'vstr':
            vstr = ''
            for _ in outs.values():
                vstr += _ + ','
            return "(%s)" % vstr[:-1] if parentheses is True else vstr[:-1]
        elif mode == '2str':
            nstr = ''
            vstr = ''
            for _ in real_colns:
                os = outs[_]
                nstr += _ + ','
                vstr += (str(os) if isinstance(os, (int, float)) else os) + ','
            return nstr[:-1],vstr[:-1]

    @staticmethod
    def dict2str(from_dict, array=None, mode=0, defv=None, parentheses=False):
        empty_str = ""
        defv = defv or {}
        vstr = ""
        # mode: 0->update set string(pstring), 1->vstrings, 2->2 string
        if mode == 0:
            for _ in array if array else from_dict.keys():
                v = from_dict.get(_)
                if v is None:
                    v = defv.get(_, empty_str)
                if isinstance(v, (int, float)) or v == 'NULL':
                    vstr += '%s=%s,' % (_, v)
                else:
                    vstr += '%s="%s",' % (_, v)
            return vstr[:-1]
        elif mode == 1:
            for _ in array if array else from_dict.keys():
                v = from_dict.get(_)
                if v is None:
                    v = defv.get(_, empty_str)
                if isinstance(v, (int, float)) or v == 'NULL':
                    vstr += '%s,' % v
                else:
                    vstr += '"%s",' % v
            return "(%s)" % vstr[:-1] if parentheses is True else vstr[:-1]
        else:
            nstr = ''
            for _ in array if array else from_dict.keys():
                v = from_dict.get(_) 
                if v is None:
                    v = defv.get(_, empty_str)
                if isinstance(v, (int, float)) or v == 'NULL':
                    vstr += '%s,' % v
                else:
                    vstr += '"%s",' % v
                nstr += _ + ','
                vstr += '%s,' % v
            return nstr[:-1],vstr[:-1]

    @staticmethod
    def dict_list_4json(datalist, fieldlist, one=False, NoneExport='', pre_processor=None):
        """[{key-1-1:val-1-1,key-1-2:val-1-2,...},{key-2-1:val-2-1,key-2-2:val-2-2,...}]"""
        # datalist: (1,2,3...), ((1,2,3..), (4,5,6...),...); v2.1
        # pre_processor: func(row-tuple-data)
        # ==== if for json-dumps, it's no need to convert
        if isinstance(fieldlist, str):
            fieldlist = fieldlist.split(',')
        if not datalist or not isinstance(fieldlist, (list,tuple)):
            loger.error('not a correct input!')
            return None
        def t2d(t):
            c = 0
            d = {}
            for _ in fieldlist:
                x = t[c]
                #d[_] = x if isinstance(x, (str, int, float)) else NoneExport if x is None else str(x)
                d[_] = str(x) if isinstance(x, DT) else x if x is not None else NoneExport
                c += 1
            return d
        def d2d(D):
            d = {}
            for _ in fieldlist:
                d[_] = D[_]
            return d
        def o2d(o):
            d = {}
            for _ in fieldlist:
                d[_] = o.__dict__[_]
            return d
        slen = len(fieldlist)
        if not isinstance(datalist[0], tuple):
            if slen < len(datalist):
                raise ValueError("length of item miss match! at less not less!")
            if one:
                return t2d(datalist)
            else:
                datalist = [datalist]
        out_list = list()
        # 必要的预处理？
        for line in datalist:
            if callable(pre_processor):
                line = pre_processor(line)
            if isinstance(line, (tuple, list)):
                out_list.append(t2d(line))
            elif isinstance(line, dict) or hasattr(line, '__getitem__'):
                out_list.append(d2d(line))
            elif hasattr(line, '__dict__'):
                out_list.append(o2d(line))
        return out_list

    @staticmethod
    def _fixed_date(v_in, onlydate=False):
        # string or date export to date
        if v_in is None:
            date = DT.today()
        elif isinstance(v_in, str):
            _len = len(v_in)
            if _len > 19:
                v_in = v_in[:19]
            if _len == 19:
                pstr = '%Y-%m-%d %H:%M:%S'
            elif _len == 16:
                pstr = '%Y-%m-%d %H:%M'
            elif _len == 10:
                pstr = '%Y-%m-%d'
            date = DT.strptime(v_in, pstr)
        elif isinstance(v_in, DT):
            date = v_in
        else:
            loger.error("Not A Date")
            return None
        return date.date() if onlydate else date

    @staticmethod
    def _date_str(v_in=None, onlydate=False):
        # input string mode of date and check-fix(if needed) to date_string; from client is string
        # MARK: str(date) = '2020-01-15 23:56:42.081807'
        if v_in is None:
            v_in = DT.today()
        if isinstance(v_in, DT):
            return str(v_in.date()) if onlydate else str(v_in)[:19]
        # v_in is string
        try:
            return re.match(r'\d{4}-\d{2}-\d{2}', v_in).group(0) if onlydate else re.match(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', v_in).group(0)
        except ValueError:
            loger.error("wrong data string: %s" % v_in)
            return None

    @staticmethod
    def argsform_checker(argsform):
        # check args form data for dangour
        if not hasattr(argsform, 'values'):
            return False
        strs = ''.join(argsform.values())
        if re.search(r'\band\b|\bor\b', strs, re.I):
            return False
        return True

    @staticmethod
    def argsform_fix(argsform):
        export = argsform.to_dict() if hasattr(argsform, 'to_dict') else argsform
        if not isinstance(export, dict):
            return None
        for k,v in export:
            export[k] = v.strip()
        return export


class simple_tbl(Qer):
    work_table = ''
    main_keys = None
    require_keys = None
    list_keys = None
    def_v = {}
    pkey = ''
    query_limit = 30
    query_max = 1000
    huge_insert_num = 200
    huge_insert_by = huge_insert_num//2
    
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
        checktbl = cls._con_pool.query_db('SHOW TABLES LIKE "%s"' % tablename, one=True)
        if checktbl:
            return True
        else:
            return cls._con_pool.execute_db(cls.create_syntax.format(tablename=tablename))

    @classmethod
    def _manage_item(cls, action, orign_data=None, pkey=0, **others):
        if action == 'new':
            # line below is newly update
            orign_data = orign_data or others
            nstr, vstr = cls.filter_dict(orign_data, colns=cls.main_keys[1:], require_keys=cls.require_keys, defv=cls.def_v, mode='2str')
            sqlcmd = 'INSERT INTO %s(%s) VALUES(%s)' % (cls.work_table, nstr, vstr)
            return cls._con_pool.execute_db(sqlcmd, get_ins_id=True)
            
        #pid = int(pkey)
        if pkey == 0:
            return
        if action == 'modify':
            pstr = cls.filter_dict(others, colns=cls.main_keys[1:], defv=cls.def_v, exists_only=True, mode='pstr')
            sqlcmd = 'UPDATE %s SET %s WHERE %s=%s' % (cls.work_table, pstr, cls.pkey, pkey)
        elif action == 'delete':
            if 'before_del' in others and not others['before_del']():
                return False
            else:
                sqlcmd = 'DELETE FROM %s WHERE %s=%s' % (cls.work_table, cls.pkey, pkey)
        elif action == 'sget':
            dbrt = cls._con_pool.query_db('SELECT %s FROM %s WHERE %s=%s' % (cls.list_keys, cls.work_table, cls.pkey, pkey), one=True)
            if dbrt:
                return dict(zip(cls.list_keys.split(','), dbrt))
        else:
            dbrt = None
            get_columns = ','.join(cls.main_keys)
            if action == 'get':
                dbrt = cls._con_pool.query_db('SELECT %s FROM %s WHERE %s=%s' % (get_columns, cls.work_table, cls.pkey, pkey), one=True)
            elif action == 'findone' and 'filterstr' in others:
                dbrt = cls._con_pool.query_db('SELECT %s FROM %s WHERE %s LIMIT 1' % (get_columns, cls.work_table, others['filterstr']), one=True)
            if dbrt:
                return dict(zip(cls.main_keys, dbrt))
            else:
                return None
        return cls._con_pool.execute_db(sqlcmd)

    @classmethod
    def _single_mod(cls, keyid, col, val, number=False):
        val = val if number else '"%s"' % val
        sqlcmd = 'UPDATE %s SET %s=%s WHERE %s=%s' % (cls.work_table, col, val, cls.pkey, keyid)
        return cls._con_pool.execute_db(sqlcmd)

    @classmethod
    def _find(cls, match_column, math_content, one=False, filterstr=None, right_match=True):
        # 关键字查找； column like "%..%"，注意不要用=类查找
        # 在match_column中查找类似match_content的项目
        if right_match:
            match_str = '{} like "{}%"'.format(match_column, math_content)
        else:
            match_str = '{} like "%{}%"'.format(match_column, math_content)
        get_columns = cls.list_keys or cls.main_keys
        if filterstr:
            sqlcmd = 'SELECT %s FROM %s WHERE %s AND %s' % (get_columns,  cls.work_table, filterstr, match_str)
        else:
            sqlcmd = 'SELECT %s FROM %s WHERE %s' % (get_columns,  cls.work_table, match_str)
        dbrt = cls._con_pool.query_db(sqlcmd)
        if not dbrt:
            return None
        if one:
            # 只查找一个的话，返回最短匹配者
            match_idx = cls.str_list(get_columns).index(match_column)
            shortest = 999
            shortest_idx = 0
            c = 0
            for r in dbrt:
                _len = len(r[match_idx])
                if _len < shortest:
                    shortest = _len
                    shortest_idx = c
                c += 1
            return dict(zip(get_columns, dbrt[shortest_idx]))
        return cls.dict_list_4json(dbrt, get_columns)

    @classmethod
    def _find_via_reg(cls, match_column, math_regexp, one=False, filterstr=None):
        # 用基于python的正则表达式查找
        if filterstr:
            sqlcmd = 'SELECT %s,%s FROM %s WHERE %s' % (cls.pkey, match_column, filterstr, cls.work_table)
        else:
            sqlcmd = 'SELECT %s,%s FROM %s' % (cls.pkey, match_column, cls.work_table)
        dbrt = cls._con_pool.query_db(sqlcmd)
        if dbrt:
            takes = []
            reger = re.compile(math_regexp)
            for r in dbrt:
                if reger.match(r[1]):
                    takes.append(r[0])
            if len(takes) > 0:
                return cls._list_items(keyids=takes)

    @classmethod
    def _list_items(cls, keyids='', lastid=None,  get_columns=None, fieldlist=None, limit=0, offset=0, filterstr='', summary=False):
        sqlcmd = 'SELECT %s FROM %s' % (cls.main_keys, cls.work_table)
        limit = limit or cls.query_limit
        if get_columns is None:
            fieldlist = cls.list_keys or cls.main_keys
            get_columns = fieldlist if isinstance(fieldlist, str) else ','.join(fieldlist)
        elif isinstance(get_columns, str):
            fieldlist = fieldlist or get_columns.split(',')
        else:
            # must be list/tuple
            get_columns = ','.join(get_columns)
            fieldlist = fieldlist or get_columns
        if keyids:
            sqlcmd = 'SELECT %s FROM %s WHERE %s in (%s)' % (get_columns, cls.work_table, ','.join(keyids) if isinstance(keyids, list) else keyids)
            dbrt = cls._con_pool.query_db(sqlcmd)
            if summary:
                total = len(dbrt) if dbrt else 0
        else:
            filterstr = filterstr or '1=1'
            if lastid and lastid > 0:
                sqlcmd = 'SELECT %s FROM %s WHERE %s>%d WHERE %s LIMIT %d' % (get_columns, cls.work_table, cls.pkey, lastid, filterstr, limit)
            else:
                sqlcmd = 'SELECT %s FROM %s WHERE %s LIMIT %d,%d' % (get_columns, cls.work_table, filterstr, offset, limit)                
            if summary:
                countcmd = 'SELECT count(*) FROM %s WHERE %s' % (cls.work_table, filterstr)
                total = cls._con_pool.query_db(countcmd, one=True)
                if not total:
                    total = 0
                    dbrt = None
                    return 0,None
                else:
                    total = total[0]
            dbrt = cls._con_pool.query_db(sqlcmd)
        if not dbrt:
            return (0,None) if summary else None
        if summary:
            return total, cls.dict_list_4json(dbrt, fieldlist)
        return cls.dict_list_4json(dbrt, fieldlist)

    @classmethod
    def _collect(cls):
        # 按表格收集数据，用于内部
        pass

    @classmethod
    def _count(cls, bystr=''):
        if bystr:
            sqlcmd = 'SELECT count(*) FROM %s WHERE %s' % (cls.work_table, bystr)
        else:
            sqlcmd = 'SELECT count(*) FROM %s' % cls.work_table
        return cls._con_pool.query_db(sqlcmd, one=True)[0]

    @classmethod
    def _mapout(cls, map_colname):
        # map: {pkey1, map_colname1, ...}
        assert map_colname in cls.main_keys
        sqlcmd = 'SELECT %s,%s FROM %s' % (cls.pkey, map_colname, cls.work_table)
        dbrt = cls._con_pool.query_db(sqlcmd)
        map_dict = {}
        if dbrt:
            for _ in dbrt:
                map_dict[_[0]] = _[1]
            return map_dict
        return map_dict

    @classmethod
    def _vget(cls, key, column, key_col=None, num_key=False, one_key=True, cols=0):
        # most of times get one column by primary key: single quick
        # key: no list!
        # num_key: the key is integer (default), and works when key_col is given
        # one_key: only one key => and return one row (qurey_db with one=True), when False: key is a list/list-string
        # cols: number of column-to-get in column, defaults 0, auto test
        # return:
        #   mysql result tuple(s) or (None, ...)
        #   maybe i shuold kick arg cols
        if cols == 0:
            cols = column.count(",") + 1
        #cols = column.count(",") + 1
        if key_col is None:
            # no need to check if num_key
            if one_key:
                sqlcmd = 'SELECT %s FROM %s WHERE %s=%s LIMIT 1' % (column, cls.work_table, cls.pkey, key)
            else:
                sqlcmd = 'SELECT %s FROM %s WHERE %s in (%s)' % (column, cls.work_table, cls.pkey, key)
            dbrt = cls._con_pool.query_db(sqlcmd, one=one_key)
            if dbrt:
                return dbrt[0] if (one_key and cols==1) else dbrt
            else:
                return None if cols==1 else (None,)*cols
        # more options
        # one_key equals one_row
        if not isinstance(num_key, bool):
            num_key = isinstance(key, (int, float)) or key.split(',')[0].isdigit()
        if one_key:
            key = key if num_key else '"%s"' % key
            sqlcmd = 'SELECT %s FROM %s WHERE %s=%s LIMIT 1' % (column, cls.work_table, key_col, key)
        else:
            key = key if num_key else '"' + key.replace(',', '","') + '"'
            sqlcmd = 'SELECT %s FROM %s WHERE %s in (%s)' % (column, cls.work_table, key_col, key)
        dbrt = cls._con_pool.query_db(sqlcmd, one=one_key)
        if dbrt:
            return dbrt[0] if (one_key and cols==1) else dbrt
        else:
            return None if cols==1 else (None,)*cols

    @classmethod
    def _rowget(cls, keyidx, getdict=False):
        # JUST GET A ROW by keyidx
        sqlcmd = "SELECT * FROM %s WHERE %s=%d" % (cls.work_table, cls.pkey, keyidx)
        dbrt = cls._con_pool.query_db(sqlcmd, one=True)
        if not dbrt:
            return None
        if getdict is False:
            return dbrt
        return dict(zip(cls.main_keys, dbrt))

    @classmethod
    def huge_insert(cls, value_list, autocolumn=None, singlecmd=True, safe=False, work_table=""):
        # value_list: [{data_dict1}, {data_dict2}, {data_dict3}, ...]
        # value_list: [[v1,v2,v3...], ...], match the autocolumn...: 
        # if autocolumn is False: all data-dict contains the same keys, a faster kvstring
        # if singlecmd is False, sqlcmd are: insert (), insert (), ...; list of sql commands
        work_table = work_table or cls.work_table
        if isinstance(value_list[0], dict):
            vmode = 'dict'
            batcher = cls.__batch_insert
        elif isinstance(value_list[0], (list, tuple)):
            vmode = 'array'
            batcher = cls.__batch_insert2
        else:
            raise ValueError("WRONG: value_list type.")
        if autocolumn is True:
            column_list = cls.main_keys[1:]
        else:
            if autocolumn is False and vmode == 'dict':
                # 只有从数据提取的字段无需校验
                column_list = list(value_list[0].keys())
            else:
                if autocolumn is None:
                    column_list = cls.str_list(cls.require_keys)
                elif isinstance(autocolumn, str):
                    column_list = [_.strip() for _ in autocolumn.split(',')]
                elif isinstance(autocolumn, (list, tuple)):
                    column_list = autocolumn
                else:
                    raise ValueError("unkown autocolumn type!")
                # 自动column，以第一个数据dict进行测试，确保包含所有需要的字段
                _testor = value_list[0]
                if vmode == 'dict' and not all([_ in _testor for _ in column_list]):
                    raise ValueError("the given column not fit with value_dict!")
                elif vmode == 'array' and len(column_list) != len(_testor):
                    raise ValueError("the given column not fit with value_list!")

        slen = len(value_list)
        if slen <= cls.huge_insert_num:
            return batcher(value_list, column_list, singlecmd=singlecmd, safe=safe, work_table=work_table)
        times = slen // cls.huge_insert_by + (1 if slen % cls.huge_insert_by > 0 else 0)
        _s = 0
        _e = 0
        for i in range(times):
            _s = i * cls.huge_insert_by
            _e = (i+1) * cls.huge_insert_by
            batcher(value_list[_s:_e], column_list, singlecmd=singlecmd, safe=safe, work_table=work_table)
            slen -= cls.huge_insert_by

    @classmethod
    def __batch_insert(cls, value_list, column_list, singlecmd=True, safe=False, work_table=""):
        def local_vs(klist, d_in, parentheses):
            vs = []
            for k in klist:
                v = d_in[k]
                if isinstance(v, str):
                    # or:
                    try:
                        float(v) == int(v)
                        vs.append(v)
                    except ValueError:
                        vs.append('"%s"' % str(v))
                    #if re.fullmatch(r'\d+(\.\d+)?', v):
                    #    vs.append(v)
                    #else:
                    #    vs.append('"' + str(v) + '"')
                elif isinstance(v, (int, float)) or v == "NULL":
                    vs.append(str(v))
                else:
                    vs.append('"' + str(v) + '"')
            return '(%s)' % ','.join(vs) if parentheses else ','.join(vs)

        work_table = work_table or cls.work_table
        column_str = ','.join(column_list)
        valuestr_list = []
        for d in value_list:
            valuestr_list.append(local_vs(column_list, d, parentheses=singlecmd))
        if singlecmd is False:
            # insert command sequence...
            insert_cmds = []
            for vs in valuestr_list:
                insert_cmds.append('INSERT INTO %s(%s) VALUES(%s)' % (cls.work_table, column_str, vs))
            if safe is False:
                insert_cmd = ';'.join(insert_cmds)
                return cls._con_pool.do_sequence(insert_cmd)
            else:
                c = 0
                con = cls._con_pool.free()
                cur = con.cursor()
                for scmd in insert_cmds:
                    try:
                        cur.execute(scmd)
                        c += 1
                    except:
                        print(cur.fetchwarnings())
                        continue
                cur.close()
                cls._con_pool.release(con)
                loger.info("safety insert %d." % c)
                return
            return cls._con_pool.do_sequence(insert_cmds)
        value_str = ','.join(valuestr_list)
        insert_cmd = 'INSERT INTO %s(%s) VALUES %s' % (cls.work_table, column_str, value_str)
        return cls._con_pool.execute_db(insert_cmd)

    @classmethod
    def __batch_insert2(cls, value_list, column_list, singlecmd=True, safe=False, work_table=""):
        def local_vs(l_in, parentheses):
            _vs = []
            for v in l_in:
                if isinstance(v, str):
                    try:
                        float(v) == int(v)
                        _vs.append(v)
                    except ValueError:
                        _vs.append('"%s"' % str(v))
                    #if re.fullmatch(r'\d+(\.\d+)?', v):
                    #    _vs.append(v)
                    #else:
                    #    _vs.append('"' + str(v) + '"')
                elif isinstance(v, (int, float)) or v == "NULL":
                    _vs.append(str(v))
                else:
                    _vs.append('"' + str(v) + '"')
            return '(%s)' % ','.join(_vs) if parentheses else ','.join(_vs)

        work_table = work_table or cls.work_table
        column_str = ','.join(column_list)
        valuestr_list = []
        for r in value_list:
            valuestr_list.append(local_vs(r, parentheses=singlecmd))
        if singlecmd is False:
            # insert command sequence...
            insert_cmds = []
            for vs in valuestr_list:
                insert_cmds.append('INSERT INTO %s(%s) VALUES(%s)' % (work_table, column_str, vs))
            if safe is False:
                insert_cmd = ';'.join(insert_cmds)
                return cls._con_pool.do_sequence(insert_cmd)
            else:
                c = 0
                con = cls._con_pool.free()
                cur = con.cursor()
                for scmd in insert_cmds:
                    try:
                        cur.execute(scmd)
                        c += 1
                    except:
                        print(cur.fetchwarnings())
                        continue
                cur.close()
                cls._con_pool.release(con)
                loger.info("safety insert %d." % c)
                return
        value_str = ','.join(valuestr_list)
        insert_cmd = 'INSERT INTO %s(%s) VALUES %s' % (work_table, column_str, value_str)
        return cls._con_pool.execute_db(insert_cmd)