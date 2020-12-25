#!/usr/bin/env python
# -*- coding: utf8
# updated: 2018/12/21; 2019/12/15
from libs import Qer

class sysconsts(Qer):
    """
    Table contains kinds of variables(tiny, small sets of infos)
    type: variable set name(type of variables)
    key: name to identified, if no title, may use key as title
    title: name to show
    value: value of variable
    value_int: if we need second value, should only be int
    extdata: if we need more data
    """
    work_table = 'sysconsts'
    main_keys = ('idx', 'type', 'subtype', 'ikey', 'title', 'value', 'value_int', 'extdata', 'status')
    quick_list = 'idx,ikey,title,value,value_int' # take less data
    decoders = {}
    encoders = {}
    pkey = 'idx'
    create_syntax = """CREATE TABLE `{tbl_name}` (\
    `idx` INT NOT NULL AUTO_INCREMENT, \
    `type` VARCHAR(48) NOT NULL,\
    `subtype` VARCHAR(32) DEFAULT NULL,\
    `ikey` VARCHAR(24) NOT NULL,\
    `title` VARCHAR(48) DEFAULT NULL,\
    `value` VARCHAR(32) DEFAULT NULL,\
    `value_int` INT DEFAULT 0,\
    `extdata` VARCHAR(128) DEFAULT NULL,\
    `status` TINYINT DEFAULT 0,\
    PRIMARY KEY (`idx`),\
    KEY `_ikey` (ikey)\
    )ENGINE = InnoDB AUTO_INCREMENT=1 CHARSET=utf8;"""
    # status: 0-normal; delete(markmode): -1;
    STA_NORMAL = 1
    STA_UNSET = 0
    STA_OFF = -1

    @classmethod
    def ini_table(cls, tblname=''):
        tblname = tblname or cls.work_table
        checktable = cls.con.query_db('show tables like "sysconsts"', one=True)
        if checktable:
            return True
        if cls.con.execute_db(cls.create_syntax.format(tbl_name=tblname)):
            cls.work_table = tblname
            return True
        return False

    @classmethod
    def update(cls):
        sqlcmd = 'SELECT DISTINCT type FROM sysconsts'
        dbrt = cls._con_pool.query_db(sqlcmd, single=True)
        if dbrt:
            del cls.alltype
            cls.alltype = set(dbrt)

    @classmethod
    def newtype(cls, typename, fkey, ftitle="", fvalue="", fvalue_int=0, extdata=''):
        # create a new type of vals with first item[status as 0]
        sqlcmd = 'INSERT INTO sysconsts(type,ikey,fmode,title,value,value_int,extdata) \
        VALUES("%s","%s","%s","%s",%d,"%s")' % (typename, fkey, ftitle, fvalue, fvalue_int, extdata)
        return cls._con_pool.execute_db(sqlcmd, get_ins_id=True)

    @classmethod
    def clear_type(cls, typename, mark=False):
        # drop type
        if mark:
            sqlcmd = 'UPDATE %s SET status=-1 WHERE type="%s"' % (cls.work_table, typename)
        else:
            sqlcmd = 'DELETE FROM %s WHERE type="%s"' % (cls.work_table, typename)
        return cls._con_pool.execute_db(sqlcmd)

    @classmethod
    def list_types(cls):
        sqlcmd = 'SELECT type,count(*) FROM %s GROUP BY type' % (cls.work_table)
        dbrt = cls._con_pool.query_db(sqlcmd)
        if dbrt:
            return cls.dict_list_4json(('typename', 'count'), dbrt)

    @classmethod
    def export(cls, datalist, decoder=None, quick=False):
        """[{key-1-1:val-1-1,key-1-2:val-1-2,...},{key-2-1:val-2-1,key-2-2:val-2-2,...}]"""
        # datalist: (1,2,3...), ((1,2,3..), (4,5,6...),...); v2.1
        # mappers: {key1: {id1:val1,id2:val2}, key2...}
        fieldlist = cls.quick_list if quick else cls.main_keys
        if quick:
            fieldlist = cls.str_list(cls.quick_list)
        else:
            cls.main_keys
        out_list = list()
        for line in datalist:
            if decoder:
                line = list(line)
                if quick:
                    line[3] = decoder(line[3])
                else:
                    line[5] = decoder(line[5])
            out = {}
            c = 0
            for _ in fieldlist:
                x = line[c]
                out[_] = x if isinstance(x, (str, int, float)) else str(x) if x is not None else None
                c += 1
            out_list.append(out)
        return out_list

    @classmethod
    def set_setcoder(cls, typename, decoder, encoder=None):
        if decoder is None:
            try:
                cls.decoders.pop(typename)
                cls.encoders.pop(typename)
            except KeyError:
                pass
            return
        if not callable(decoder) or not callable(encoder):
            raise ValueError("E: Solver Must be callable/encoder!")
        dbrt = self._con_pool.query_db('SELECT idx FROM %s WHERE type="%s" LIMIT 1' % (cls.work_table, typename), one=True)
        if dbrt and dbrt[0] > 0:
            cls.decoders[typename] = decoder
            cls.encoders[typename] = encoder

    def __init__(self, typename, precheck=False, work_table=None, decoder=None, encoder=None):
        super(sysconsts, self).__init__()
        self.con = self.__class__._con_pool
        # main_keys: col_name_1,col_name2,...; mapper: output_name_1,output_name_2,...
        self.work_table = work_table or self.__class__.work_table
        if precheck:
            sqlcmd = 'SELECT idx FROM %s WHERE type="%s" LIMIT 1' % self.work_table
            try:
                #self.__class__._con_pool.query_db(sqlcmd, one=True)[0]
                self.con.query_db(sqlcmd, one=True)[0]
            except:
                raise RuntimeError("type: %s is Not Exists!" % typename)
        self.type = typename
        self.main_keys = self.__class__.main_keys
        self.quick_list = self.__class__.quick_list
        self.decoder = decoder or self.__class__.decoders.get(typename)
        self.encoder = encoder or self.__class__.encoders.get(typename)
    
    def data_coder(self, decoder, encoder):
        # decoder is function
        if callable(decoder):
            self.decoder = decoder
            self.encoder = encoder
        else:
            return None
        return self
        
    def data(self, idx=0, key=None, subkey=None, onlyval=False):
        qstr = ','.join(self.__class__.main_keys)
        if idx:
            dbrt = self.con.query_db('SELECT %s FROM %s WHERE idx=%s AND status>=0' % (qstr, self.work_table, idx), one=True)
        elif key:
            dbrt = self.con.query_db('SELECT %s FROM %s WHERE type="%s" AND ikey="%s"' % (qstr, self.work_table, self.type, key), one=True)
        else:
            raise ValueError("one of idx/key should be given!")
        if dbrt:
            if self.decoder:
                dbrt = list(dbrt)
                value = self.decoder(dbrt[5])
                dbrt[5] = value
            else:
                value = dbrt[5]
            if onlyval:
                return value
            #return dict(zip(self.mapper, dbrt))
            return {'idx': dbrt[0], 'type':dbrt[1], 'subtype': dbrt[2], 'key': dbrt[3], 'title': dbrt[4], 'value': value, 'value_int': dbrt[6], 'extdata': dbrt[7], 'status': dbrt[8]}
        else:
            return dbrt

    def value(self, idx=0, key=None, target=1, getdict=False):
        # target:
        # 1: value, 2: value_int, 4: extdata, 3: value-value_int, 5: value-extdata, 6: value_int-extdata, 7: value-value_int-extdata
        cols = ""
        if target & 1:
            cols = 'value'
        if (target & 0b10) >> 1:
            cols += ',value_int' if cols else 'value_int'
        if target >> 2:
            cols += ',extdata' if cols else 'extdata'
        if key:
            sqlcmd = 'SELECT %s FROM %s WHERE type="%s" AND ikey="%s" LIMIT 1' % (cols, self.work_table, self.type, key)
        else:
            sqlcmd = 'SELECT %s FROM %s WHERE type="%s" AND idx=%d' % (cols, self.work_table, self.type, idx)
        dbrt = self.con.query_db(sqlcmd, one=True)
        if getdict and dbrt:
            return dict(zip(cols, dbrt))
        return dbrt

    def single_col(self, colname):
        # 本类，单1列
        return self.con.query_db('SELECT %s FROM %s WHERE type="%s"' % (colname, self.work_table, self.type), one=True)

    def getlist(self, limit=20, offset=0, quick=True):
        if quick:
            sqlcmd = 'SELECT %s FROM %s WHERE type="%s" LIMIT %s,%s' % (self.__class__.quick_list, self.work_table, self.type, offset, limit)
        else:
            sqlcmd = 'SELECT * FROM %s WHERE type="%s" LIMIT %s,%s' % (self.work_table, self.type, offset, limit)
        dbrt = self.con.query_db(sqlcmd)
        if dbrt:
            #return self.dict_list_4json(dbrt, self.mapper)
            return self.export(dbrt, quick=quick, decoder=self.decoder)
        else:
            return []

    def simplelist(self, bysubtype=None, byextdata=None, filterstr=None, k_v_mode=False, quick=True):
        # JUST LIST ALL
        sqlcmd = 'SELECT %s FROM %s WHERE type="%s"' % (self.quick_list if quick else ','.join(self.__class__.main_keys), self.work_table, self.type)
        if bysubtype:
            sqlcmd += ' AND subtype="%s"' % bysubtype
        if byextdata:
            sqlcmd += ' AND extdata="%s"' % byextdata
        if filterstr:
            sqlcmd += ' AND %s' % filterstr
        dbrt = self.con.query_db(sqlcmd)
        if not dbrt:
            return []
        if not k_v_mode:
            #return self.dict_list_4json(dbrt, self.main_keys)
            return self.export(dbrt, quick=quick, decoder=self.decoder)
        else:
            # k_v mode: {key: {idx, value, value_int, extdata, status}, ...}
            # for '_' may used in title/type name, so split with ':'
            outs = {}
            for row in dbrt:
                outs[dbrt[3]] = dict(idx=dbrt[0], subtype=dbrt[2], title=dbrt[4], \
                    value=self.decoder(dbrt[5]) if self.decoder else dbrt[5], value_int=dbrt[6], extdata=dbrt[7], status=dbrt[8])
            return outs

    def setitem(self, key, value, subtype="", title="", value_int=0, extdata=''):
        # insert or update
        if self.encoder:
            value = self.encoder(value)
        find_sql = 'SELECT * FROM %s WHERE type="%s" AND ikey="%s"' % (self.work_table, self.type, key)
        sqlcmd = u'INSERT INTO {table}(type,subtype,ikey,title,value,value_int,extdata) SELECT "{type}","{subtype}","{ikey}","{title}","{value}",{value_int},"{extdata}" \
        FROM dual WHERE NOT EXISTS ({find_sql})'.format(table=self.work_table, type=self.type, ikey=key, subtype=subtype, title=title, value=value, \
            extdata=extdata, value_int=value_int, find_sql=find_sql)
        return self.con.execute_db(sqlcmd, get_ins_id=True)

    def setitems(self, items):
        # batch set items, insert or update
        # some with rid > 0 => update; and some without a rid or rid<=0, add new;
        # items: list of dict
        insert_sql = 'INSERT INTO {}(type,subtype,ikey,title,value,value_int,extdata) VALUES %s'.format(self.work_table)
        update_sql = 'UPDATE {} SET %s WHERE idx=%s'.format(self.work_table)
        defv = {'type': self.type, 'value_int': 0}
        ins_seq = []
        upd_seq = []
        for item in items:
            if self.encoder:
                item['value'] = self.encoder(item['value'])
            if 'idx' in item:
                idx = int(item['idx'])
                upd_seq.append(update_sql % (self.dict2str(item, self.main_keys[1:], 0, defv), idx))
            else:
                ins_seq.append('(%s)' % self.dict2str(item, self.main_keys[1:], 1, defv))
        insert_cmd = insert_sql % ','.join(ins_seq)
        update_cmd = ';'.join(upd_seq)
        if len(ins_seq) > 0:
            self.con.execute_db(insert_cmd)
        if len(upd_seq) > 0:
            self.con.do_sequence(update_cmd)
        return True

    def newitem(self, key, subtype="", title='', value='', value_int=0, extdata='', precheck=False):
        if precheck:
            sqlcmd = 'SELECT count(*) FROM sysconsts WHERE type="%s" AND ikey="%s"' % (self.type, key)
            if self.con.query_db(sqlcmd, one=True):
                return -1
        if self.encoder and value:
            value = self.encoder(value)
        sqlcmd = 'INSERT INTO %s(type,subtype,ikey,title,value,value_int,extdata) VALUES("%s", "%s", "%s", "%s", "%s", %d, "%s")' % \
        (self.work_table, self.type, subtype, key, title, value, value_int, extdata)
        return self.con.execute_db(sqlcmd, get_ins_id=True)

    def newitems(self, datas):
        keys = self.main_keys[1:]
        keystr = ','.join(keys)
        defv = {'type': self.type, 'value': '', 'value_int': 0, 'extdata': ''}
        item_strs = []
        for item in datas:
            if 'value' in item and self.encoder:
                item['value'] = self.encoder(item['value'])
            vstr = ""
            for _ in keys:
                v = item.get(_) or defv.get(_, "")
                v = str(v) if isinstance(v, (int, float)) or v.isdigit() else '"%s"' % v
                vstr += v + ","
            vstr = "(%s)" % vstr[:-1]
            item_strs.append(vstr)
        vstrs = ','.join(item_strs)
        sqlcmd = 'INSERT INTO %s(%s) VALUES %s' % (self.work_table, keystr, vstrs)
        return self.con.execute_db(sqlcmd)

    def flushitems(self, datas):
        # remove and news
        idxs = []
        for _ in datas:
            idxs.append(str(_['idx']))
        sqlcmd = 'DELETE FROM %s WHERE idx in (%s)' % (self.work_table, ','.join(idxs))
        if self.con.us_execute_db(sqlcmd) is not False:
            # could be 0, del with empty
            return self.newitems(datas)
        else:
            raise RuntimeError("Counld not clear type: %s" % self.type)

    def delitem(self, idx=0, ikey="", bymark=False):
        wstr = 'idx=%d' % idx if idx > 0 else 'type="%s" AND ikey="%s"' % (self.type, ikey)
        if bymark:
            sqlcmd = 'UPDATE %s SET status=-1 WHERE %s' % (self.work_table, wstr)
        else:
            sqlcmd = 'DELETE FROM %s WHERE %s' % (self.work_table, wstr)
        return self.con.execute_db(sqlcmd)

    def set_value(self, idx=0, ikey="", value="", value_int=None):
        ustr = 'value="%s"' % value
        if isinstance(value_int, int):
            ustr += ' value_int=%d' % value_int
        if idx:
            sqlcmd = 'UPDATE %s SET %s WHERE idx=%d' % (self.work_table, ustr, idx)
        elif ikey:
            sqlcmd = 'UPDATE %s SET %s WHERE type="%s" AND ikey="%s"' % (self.work_table, ustr, self.type, ikey)
        else:
            return False
        return True if self.con.execute_db(sqlcmd) else False

    def set_valueint(self, idx=0, ikey="", value_int=0):
        if idx:
            sqlcmd = 'UPDATE %s SET value_int=%d WHERE idx=%d' % (self.work_table, value_int, idx)
        elif ikey:
            sqlcmd = 'UPDATE %s SET value_int=%d WHERE type="%s" AND ikey="%s"' % (self.work_table, self.type, ikey)
        return True if self.con.execute_db(sqlcmd) else False

    def moditem(self, idx, subtype=None, key='', title='', value='', value_int=0, extdata=''):
        sqlcmd = ''
        if subtype:
            sqlcmd += ' subtype="%s"' % subtype
        elif key:
            sqlcmd += ' ikey="%s"' % key
        elif title:
            sqlcmd += ' title="%s"' % title
        elif value:
            sqlcmd += ' value="%s"' % value
        elif value_int:
            sqlcmd += ' value_int=%d' % value_int
        elif extdata:
            sqlcmd += ' extdata="%s"' % extdata
        if len(sqlcmd) == 0:
            return None
        sqlcmd = 'UPDATE %s SET(%s) WHERE idx=%s' % (self.work_table, sqlcmd, idx)
        return self.con.execute_db(sqlcmd)