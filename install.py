#!/usr/bin/env python
# -*- coding: utf8
#
import os
import sys
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


def about_crontab(cronfile=None):
    if os.name == "nt":
        print("windows not support!")
        return
    from crontab import CronTab
    tabs = [{'name': 'clear_caches'}, {'name': 'new_year'}]
    if cronfile:
        file_cron = CronTab(tabfile='self_maintain.tab')
    else:
        file_cron = CronTab(tabfile='/etc/crontab', user=False)
    job1 = file_cron.new(command='python %s%sself_maintain.py clear_caches' %(os.getcwd(), os.sep))
    job1.hour.on(1)
    job2 = file_cron.new(command='python %s%sself_maintain.py new_year' %(os.getcwd(), os.sep))
    job2.month.on(6, 7, 8)
    file_cron.write()
    

if __name__ == '__main__':
    con = test_db()
    if con:
        create_tables(con)
        check_folders()
        finish(con)
        print("install done!")
    else:
        print("ERROR")
    #about_crontab()