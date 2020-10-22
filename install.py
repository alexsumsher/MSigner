#!/usr/bin/env python
# -*- coding: utf8
#
import os
import sys
import logging

loger = logging.getLogger()

thisver = print(sys.version_info[0])
requires = ['flask', 'mysql.connector', 'xlrd', 'xlwt', 'openpyxl', 'python-crontab', 'requests']
if input("是否跳过需求包安装？") != 'y':
    for p in requires:
        # pip3 for server install py2 and py3
        os.system('pip3 install %s' % p)

#from sys_config import cur_config, logging
from sys_config import cur_config
import mysql.connector as mcr
from modules import _all_tables

STEP = 0
PATH = os.getcwd()

def test_db():
    """create database %s default charset utf8mb4 collate utf8mb4_general_ci;"""
    global STEP
    print("database testing...")
    svr = cur_config.dbserver
    try:
        con = mcr.connect(**svr)
    except:
        print("data base not found!")
        print(str(svr))
        return False
    STEP += 1
    return con

def single_table(con, tbl_obj):
    # 单表
    if isinstance(tbl_obj, str):
        for tbl in _all_tables:
            if tbl.__name__ == tbl_obj:
                tbl_obj = tbl
                break
    if not hasattr(tbl_obj, 'work_table'):
        print("unkonwn target")
        return
    cur = con.cursor()
    try:
        #cur.execute("DROP TABLE IF EXISTS %s;" % tbl_obj.work_table)
        #1142 (42000): DROP command denied to user 'dktest_a1'@'122.238.129.197' for table 'project_jobs'
        cur.execute('DROP TABLE IF EXISTS %s' % tbl_obj.work_table)
        sqlcmd = tbl_obj.create_syntax.format(tbl_name=tbl_obj.work_table)
        print(sqlcmd)
        cur.execute(sqlcmd)
        return tbl_obj.work_table
    except Exception as e:
        print(e)
        print(f"create table: {tbl_obj.work_table} failure!")
    finally:
        cur.close()
        con.close()

def create_tables(con):
    """
    exam_mgr: exam_table
    exam_score: examscore_{yearid}
    class_score: score_{classid}
    other: score_update
    """
    global STEP
    cur = con.cursor()
    print("clear all tables!")
    cur.execute("SHOW TABLES")
    dbrt = cur.fetchall()
    for tbl in dbrt:
        print("table %s to drop" % tbl[0])
        cur.execute('DROP TABLE %s' % tbl[0])
    print("create basic tables...")
    for tbl in _all_tables:
        try:
            print(f"create table: {tbl.work_table}")
            cur.execute(tbl.create_syntax.format(tbl_name=tbl.work_table))
        except mcr.Error as err:
            print("sql error %s: %s: %s" % (tbl, err.errno, err.msg))
            continue
    cur.close()
    STEP += 1
    return True

def check_folders(flist=None):
    fds = cur_config.folders
    basefd = cur_config.folder('base_fd')
    if not os.path.exists(basefd):
        raise RuntimeError("base folder not exists!")
    os.chdir(basefd)
    for f,p in fds.items():
        print("check fd: %s create fd if needed!" % f)
        if not os.path.exists(p):
            os.path.mkdir(p)
            print("folder %s is created!" % p)
        else:
            print("folder %s is exists!" % p)
    return True

def finish(con):
    global PATH
    global STEP
    tpth = os.path.join(PATH, 'inited')
    if os.path.exists(tpth):
        try:
            os.remove(tpth)
        except IOError:
            pass
    with open(os.path.join(PATH, 'installed'), 'w') as f:
        f.write('installed\r\n')
    con.shutdown()
    con.close()
    # set prodction
    os.system("export FLASK_ENV=production")
    STEP += 1
    return True


if __name__ == '__main__':
    action = sys.argv[1]
    if len(sys.argv) == 4:
        con = test_db(sys.argv[3])
    else:
        con = test_db()
    if con:
        if action == 'single_table':
            print(single_table(con, sys.argv[2]))
            sys.exit(0)
        create_tables(con)
        if action == 'onlydb':
            loger.info("onlydb done")
            finish(con)
            sys.exit(0)
        check_folders()
        finish(con)
        loger.info("install done!")
    else:
        loger.error("ERROR")