# -*- coding:utf-8
"""
MySQL Database Connection.
change to fit for poolo class.
"""
import MySQLdb
import logging
import time
#   for com_con
from random import random as rdm
from threading import Lock
logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-10s) %(message)s')

class server_info:
    server_info = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'dbuser',
        'passwd': 'dbpasswd',
        'db': 'db',
        'charset': 'utf8'
    }

    def __init__(self, **configure):
        self.__dict__ = server_info.server_info
        if 'host' in configure:
            self.host = configure['host']
        if 'port' in configure:
            self.port = configure['port']
        if 'user' in configure:
            self.user = configure['user']
        if 'passwd' in configure:
            self.user = configure['passwd']
        if 'db' in configure:
            self.user = configure['db']

    def __getitem__(self, item):
        return self.__dict__.get(item)

    @property
    def info(self):
        return self.__dict__


class mdb_mysql(object):

    @classmethod
    def add_prop(cls, pname, defv=None):
        if pname not in cls.__dict__:
            cls.__dict__[pname] = defv

    def __init__(self, server_args, **extargs):
        self.server_info = server_args.info if isinstance(server_args, server_info) else server_args
        self.dbname = self.server_info['db']
        self.conn = None
        self.last_cmd = ''

        if self.connect_db() != 1:
            return None
        # ready=0, closed=-1, using=1
        self._mark = extargs.get('mark', '')
        self.stat = 0

    def __getitem__(self, query_string):
        cmd_arr = query_string.split(';')
        if len(cmd_arr) > 1:
            return self.do_sequence(cmd_arr)
        else:
            operation = query_string.split(' ')[0]
            if operation.lower() in ('insert', 'update', 'delete'):
                return self.execute_db(query_string)
            else:
                rt = self.query_db(query_string)
                return rt[0] if rt and len(rt) == 1 else rt
                
    # @property
    # def lastInsertID(self):
    #     return self.conn.insert_id()
    #     
    @property
    def mark(self):
        return self._mark

    @mark.setter
    def mark(self, mark):
        self._mark = mark
    
    def free(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError

    @property
    def lastcmd(self):
        return self.last_cmd

    def assign_connection(self, con):
        if self.check_conn(con) < 2:
            print 'not a correct connection pass in!'
            return 0
        else:
            self.conn = con
            return 1

    def connect_db(self):
        if self.conn:
            constat = self.check_conn()
            if constat == 2:
                print 'connect exists!'
                return 1
            elif constat == 1:
                self.conn.close()
        try:
            self.conn = MySQLdb.connect(*[], **self.server_info)
            self.conn.autocommit(True)
        except MySQLdb.DatabaseError as err:
            print 'Error on connecting to DB Server: %s' % err
            return 0
        if self.check_conn >=2:
            return 1
        else:
            return 0

    def get_cur(self):
        try:
            return self.conn.cursor()
        except:
            if self.connect_db() == 1:
                return self.conn.cursor()
            else:
                raise ValueError('not get cursor!')

    def change_db(self, dbname):
        try:
            self.conn.select_db(dbname)
        except MySQLdb.MySQLError as err:
            print 'MySQL Server Error: %s' % err
            return 0
        self.dbname = dbname
        self.server_info['db'] = dbname
        return 1

    def ready(self):
        """
        work with opooler: if opooler->down==close connection; on opooler i_get(wait->work), do nothing until using
        it with execute_db or querydb, the execute method would auto connect to server first...
        stat: -1(no work), 0(wait/idel), 1(working/using/binded);
        set to working mode.
        """
        if self.check_conn() == 2 or self.connect_db() == 1:
            self.stat = 1
        else:
            self.stat = -1
        return self.stat

    def idle(self):
        if self.check_conn() == 2 or self.connect_db() == 1:
            self.stat = 0
        else:
            self.stat = -1
        return self.stat

    def close(self):
        #   if conn is exists and usable, conn.__str__():<_mysql.connection open to '192.168.1.191' at 11888f8>
        #   if conn is exists and closed, conn.__str__():<_mysql.connection closed at 3201fc8>
        if self.conn and self.conn.__str__().split()[1] == 'open':
            try:
                self.conn.close()
            except MySQLdb.MySQLError as err:
                print 'MySQL Server Error: %s' % err
        self.conn = None
        return 1

    def check_conn(self, con=None):
        """
        return -1 if not a MySQLdb.Connection, 0 if is a connection but closed,
        1 if opened but not connect to a correct server, 2 if server ok!
        """
        target = con if con else self.conn
        i = -1
        if isinstance(target, MySQLdb.connections.Connection):
            i += 1
            if target.__str__().split()[1] == 'open':
                i += 1
                i += 1 if target.get_host_info().split()[0] == self.server_info['host'] else 0
        return i

    def __enter__(self):
        self.execute_db('START TRANSACTION')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.execute_db('COMMIT')

    def execute_db(self, sqlcmd, args=None, cur=None):
        #   for debug:
        print sqlcmd
        #   在执行之前可能需要做一些cursor的处理，故可以先get_cur然后传入cur的方式来执行execute_db
        if self.conn is None:
            if self.connect_db() == 0:
                print 'SQL Server error on connect! Can not query!'
                return 0
        vcur = cur or self.get_cur()
        rt = 0
        try:
            rt = vcur.execute(sqlcmd, args)
        except MySQLdb.ProgrammingError:
            self.conn.store_result()
            self.conn.next_result()
            rt = vcur.execute(sqlcmd, args)
        except MySQLdb.OperationalError:
            logging.warning('Server error! Cannot execute SQL statement!')
            if not cur:
                #   if cur, execute invoked by query, return false
                return -1
            else:
                self.close()
                if self.connect_db() != 1:
                    logging.warning('Server Down!')
                    return None
                else:
                    vcur = self.get_cur()
                    rt = vcur.execute(sqlcmd, args)
        finally:
            self.last_cmd = sqlcmd
            # iid = 0
            # if rt and sqlcmd[:6].lower == 'insert':
            #     iid = vcur.execute('SELECT LAST_INSERT_ID();')
            #     rrt = iid,rt
            # else:
            # rrt = rt
            if not cur:
                vcur.close()
        return rt

    def us_execute_db(self, sqlcmd, args=None):
        logging.warning('unsafe execute db!')
        cur = self.get_cur()
        rt = 0
        try:
            cur.execute('SET SQL_SAFE_UPDATES=0;')
            self.last_cmd = sqlcmd
        except MySQLdb.ProgrammingError:
            self.conn.store_result()
            self.conn.next_result()
            cur.execute('SET SQL_SAFE_UPDATES=0;')
            rt = cur.execute(sqlcmd, args)
        except MySQLdb.OperationalError:
            logging.warning('Server error! connection is closed!retry!')
            self.close()
            if self.connect_db() != 1:
                return None
            else:
                cur = self.get_cur()
                cur.execute('SET SQL_SAFE_UPDATES=1;')
                rt = cur.execute(sqlcmd, args)
        except MySQLdb.Error:
            logging.warning('Server error! Cannot execute SQL statement!')
            self.close()
            return 0
        finally:
            cur.execute('SET SQL_SAFE_UPDATES=1;')
            cur.close()
        return rt

    #   查询的结果是一个tuple，所以需要其中第一个参数时（无论one是否true）都应该用[0]
    #   fetchall的结果是由tuple组成的list，one=True表示读取第一个tuple
    #   query+tuple查询方式:cursor.execute('select * from user where name=? and pwd=?', ('abc', '123456'))
    def query_db(self, query, args=None, incur=None, one=False):
        if incur:
            cur = incur
        else:
            cur = self.get_cur()
        rt = 0
        rv = None
        rt = self.execute_db(query, args=args, cur=cur)
        #   if con may down, reconnect and query again.
        if rt == -1 and self.check_conn < 2:
            self.close()
            if self.connect_db() == 1:
                cur = self.get_cur()
                rt = self.execute_db(query, args=args, cur=cur)
            else:
                return None
        if rt:
            rv = cur.fetchone() if one else cur.fetchall()
        if not incur:
            cur.close()
        return rv[0] if rv and len(rv) == 1 else rv

    #   handling for huge number of insert
    def huge_insert(self, table, colums, values, seq_len=1000):
        assert len(colums) == len(values[0])
        orign_command = 'INSERT INTO {0} ({1}) VALUES %s'.format(table, ','.join(colums))
        value_str = ''
        length = len(values)
        loop_count = length / seq_len + (1 if length % seq_len > 0 else 0)
        counter = 0
        cur = self.get_cur()
        for loop in xrange(loop_count):
            cc = 0
            for line in values:
                cc += 1
                line_str = '(%s),' % ','.join(map(lambda x: '"%s"' % x if isinstance(x, (str, unicode)) else str(x), line))
                value_str += line_str
            sql_command = (orign_command % value_str)[:-1]
            if cur.execute(sql_command):
                counter += cc
            else:
                print 'Error: huge_insert: on loop==%d' % loop
        cur.close()
        return '%s/%s' % (counter, length)

#   from v1.0: removed transaction functons

    def execute_many(self, sqlstr, args):
        """insert into table (col1, col2...) values (%s, %s...), [(var1-1, var1-2...), (var2-1, var2-2)...]"""
        if self.conn is None:
            if self.connect_db() == 0:
                raise MySQLdb.MySQLError
        cur = self.get_cur()
        rt = 1
        try:
            cur.executemany(sqlstr, args)
        except MySQLdb.MySQLError:
            logging.error('not success on execute_many')
            rt = 0
        finally:
            cur.close()
        return rt

    def do_sequence(self, sql_seq, ignore=False):
        # batch execute a list of sql command
        if self.conn is None:
            if self.connect_db() == 0:
                logging.error('can not connect to database!')
                return 0
        cur = self.get_cur()
        rts = []
        sql_seq = sql_seq if isinstance(sql_seq, (list,tuple)) else sql_seq.split(';')
        for sql_cmd in sql_seq:
            rt = 0
            try:
                rt = cur.execute(sql_cmd)
            except MySQLdb.OperationalError:
                logging.warning('Server error! Cannot execute SQL statement!')
                self.close()
                if self.connect_db() != 1:
                    logging.warning('Server error! Cannot connect to server!')
                    return 0
                else:
                    cur = self.get_cur()
                    rt = cur.execute(sql_cmd)
            except MySQLdb.MySQLError:
                logging.warning('mysql error on command: %s' % sql_cmd)
                if not ignore:
                    cur.close()
                    return 0
                else:
                    rts.append(rt)
                    continue
            if rt and sql_cmd[:6].lower() == 'select':
                rtv = cur.fetchall()
                rts.append(rtv if len(rtv)>1 else rtv[0])
            else:
                rts.append(rt)
        cur.close()
        return rts

    def do_transaction(self, sql_seq, ignore=False):
        """transaction mode"""
        if self.conn is None:
            if self.connect_db() == 0:
                logging.error('can not connect to database!')
                return 0
        cur = self.get_cur()
        cur.execute('BEGIN')
        rts = []
        for sql_cmd in sql_seq:
            rt = 0
            try:
                rt = cur.execute(sql_cmd)
            except MySQLdb.MySQLError:
                logging.warning('mysql error on command: %s' % sql_cmd)
                if not ignore:
                    self.conn.rollback()
                    cur.close()
                    return 0
                else:
                    self.conn.store_result()
                    self.conn.next_result()
                    rts.append(rt)
                    continue
            if rt and sql_cmd[:6].lower() == 'select':
                rtv = cur.fetchall()
                rts.append(rtv if len(rtv)>1 else rtv[0])
            else:
                rts.append(rt)
        self.conn.commit()
        cur.close()
        return rts

    def do_sql_script(self, sql_scr_str):
        if self.conn is None:
            if self.connect_db() == 0:
                raise MySQLdb.MySQLError('can not connect to database file')
        self.conn.executescript(sql_scr_str)
        return 1


class com_con(object):
    length = 10
    C_free = 200
    C_recv = 0

    #   -1: not inited; 1: working; 0:shutdown
    #   
    def __init__(self, sql_obj, con_info, length=0, atonce=True):
        self.length = length or self.__class__.length
        self.sqo = sql_obj
        self.cif = con_info
        self.finger = 0
        self.ilock = Lock()
        self.status = -1
        self.conlist = []
        self.staticlist = []
        self.curcon = None
        if atonce:
            self.inilist(sql_obj, con_info)

    def __getitem__(self, sqlcmds):
        con = self.__take_kick()
        if con:
            try:
                rt = con[sqlcmds]
            except:
                rt = None
            finally:
                self.__take_kick(con)
            return rt
        else:
            raise RuntimeError('NO connection to take, with current finger=%s' % self.finger)

    def inilist(self, sql_obj, con_info):
        if self.status > 0:
            return
        self.ilock.acquire()
        if len(self.conlist) > 0:
            for i in xrange(len(self.conlist)):
                self.conlist.pop().close()
        if len(self.staticlist) > 0:
            for i in xrange(len(self.staticlist)):
                self.staticlist.pop()
        if self.status == -1:
            self.staticlist = [None] * self.length
            for i in xrange(self.length):
                con = sql_obj(con_info)
                self.conlist.append(con)
                self.staticlist[i] = con
                time.sleep(0.05)
        elif self.status == 0:
            i = 0
            for con in self.staticlist:
                t = con.connect_db()
                if t == 0:
                    self.conlist.remove(con)
                    self.conlist.append(sql_obj(con_info))
                    del con
                i += 1
            if i < self.length:
                self.conlist.extend([sql_obj(con_info) for x in xrange(self.length - i)])
            self.staticlist = [None] * self.length
            for t in xrange(len(self.conlist)):
                self.staticlist[t] = self.conlist[t]
        self.status = 1
        self.ilock.release()
        return self.status

    def shutdown(self):
        self.ilock.acquire()
        for con in self.staticlist:
            con.close()
            time.sleep(0.05)
        self.status = 0
        self.ilock.release()

    def __batch_recovery(self):
        for con in self.staticlist:
            if con.mark == self.__class__.C_free:
                con.mark = self.__class__.C_recv
                self.conlist.append(con)
                self.finger -= 1
        return self.finger

    def __take_kick(self, con=None):
        if con:
            self.conlist.append(con)
            self.finger -= 1
            return self.finger
        if self.status <= 0:
            if self.inilist(self.sqo, self.cif) != 1:
                raise RuntimeError('Cannot Initial the Pool!')
        self.ilock.acquire()
        if self.finger >= self.length:
            self.__batch_recovery()
            if self.__finger >= self.length:
                for i in xrange(5):
                    time.sleep(round(rdm(),1))
                    if self.finger < self.length:
                        break
                if i >= 4:
                    self.ilock.release()
                    return None
        con = self.conlist.pop(0)
        self.finger += 1
        self.ilock.release()
        return con

    def free(self):
        con = self.__take_kick()
        if con:
            con.mark = self.__class__.C_free
            return con
        else:
            return None

    def release(self, con=None):
        if con:
            return self.__take_kick(con)
        i = 0
        for con in self.staticlist:
            if con.mark == self.__class__.C_free:
                con.mark = self.__class__.C_recv
                self.__take_kick(con)
                i += 1
        return i

    def __enter__(self):
        if self.curcon:
            raise RuntimeError

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.curcon:
            self.__take_kick(self.curcon)
            self.curcon = None

    def execute_db(self, cmd, get_ins_id=False):
        con = self.__take_kick()
        if con:
            try:
                rt = con.execute_db(cmd)
            except:
                rt = None
            finally:
                self.__take_kick(con)
            if get_ins_id and rt:
                rt = con.query_db('SELECT LAST_INSERT_ID;')[0]
            return rt
        else:
            raise RuntimeError('NO connection to take, with current finger=%s' % self.finger)

    def query_db(self, cmd, one=False):
        con = self.__take_kick()
        if con:
            try:
                rt = con.query_db(cmd, one=one)
            except:
                rt = None
            finally:
                self.__take_kick(con)
            return rt
        else:
            raise RuntimeError('NO connection to take, with current finger=%s' % self.finger)

    def do_sequence(self, sql_seq, ignore=False):
        con = self.__take_kick()
        if con:
            try:
                rt = con.do_sequence(sql_seq, ignore=ignore)
            except:
                rt = None
            finally:
                self.__take_kick(con)
            return rt
        else:
            raise RuntimeError('NO connection to take, with current finger=%s' % self.finger)


if __name__ == '__main__':
    server = server_info().info
    testdbc = mdb_mysql(server)
    if testdbc.connect_db() == 1:
        print 'YES'
    else:
        print 'NO'
    print testdbc['show tables;']
    testdbc.close()
