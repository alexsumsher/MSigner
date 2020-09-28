#!/usr/bin/env python
# -*- coding: utf8
# 
import os
import sys
import shutil
import csv
# for template mode, we have to use openpyxl with xlsx
import xlwt
# https://xlrd.readthedocs.io/en/latest/api.html#xlrd-sheet
import xlrd
# https://xlwt.readthedocs.io/en/latest/
#from openpyxl import load_workbook, Workbook
import uuid
import time

from localdata import binfile
# 
# export csv
# export excel
class xltpl(object):
    # a template object for excel
    # a template def by 2 file: exel file + defination file(.def)
    workfd = ''
    templates = [] # name: basename
    EXT = 'def'
    maxrow = 100
    maxcol = 30

    @classmethod
    def gen_by_xls(cls, xfilename):
        # create a def from xlsfile (0,0->100,30), load "$$keyname"
        xfilepath = os.path.join(cls.workfd, xfilename)
        if not os.path.exists(xfilepath):
            raise ValueError("NOT found xls file!")
        xfile = xlrd.open_workbook(xfilepath)
        # for cells merging we have to formatting_info=True
        tbl = xfile.sheets()[0]
        export = []
        maxrow = tbl.nrows - 1 #count of rows - 1
        maxcol = tbl.ncols - 1
        # for row & for col: index error on a merged_cell
        # we can use: row_values for a list of values instead
        for r in xrange(maxrow):
            c = 0
            for v in tbl.row_values(r):
                if v.startswith('$$'):
                    key = v.strip()[2:]
                    export.append([key, r, c])
                c += 1
        return cls.add(xfilename, export)

    @classmethod
    def add(cls, xlsfilename, defdata):
        # defdata a data object
        if not os.path.exists(os.path.join(cls.workfd, xlsfilename)):
            raise ValueError("XLS FILE: %s NOT FOUND IN %s!" % (xlsfilename, cls.workfd))
        if not isinstance(defdata, list):
            raise ValueError("not list")
        deffile = os.path.splitext(xlsfilename)[0] + '.' + cls.EXT
        ofile = binfile(cls.workfd)
        return ofile.save_data(defdata, deffile)
    
    def __init__(self, name, folder=None):
        folder = folder or self.__class__.workfd
        xlspath = os.path.join(folder, name + '.xls')
        defpath = os.path.join(folder, name + '.' + self.__class__.EXT)
        if os.path.exists(xlspath) and os.path.exists(defpath):
            self.name = name
            self.folder = folder
        else:
            raise ValueError("NOT FOUND TEMPLATE!")

    def __getname(self, nametype=0):
        # 0=>defname; 1/else=>xlsname
        return self.name + '.' + self.__class__.EXT if nametype == 0 else self.name + '.xls'

    def __load_bindef(self):
        self.defdata = binfile(self.folder).load_data(self.__getname())

    def update(self, defdata):
        if isinstance(defdata, list):
            self.defdata = defdata
            deffile = self.name + '.' + self.__class__.EXT
            return binfile(self.folder).save_data(self.defdata, deffile)

    def export(self, onlykeys=False):
        self.__load_bindef()
        if onlykeys:
            return [_[0] for _ in self.defdata]
        else:
            return self.defdata


class wfile(object):
    workfd = ''

    @classmethod
    def set_folder(cls, fd):
        assert os.path.isfolder(fd) and os.path.exists(fd)
        self.workfd = fd

    def __init__(self, datalist, headrow=None, headfirst=False):
        if isinstance(datalist, (str, unicode)):
            self.datalist = self._serial(datalist)
        else:
            assert isinstance(datalist, list)
        if headrow is None and headfirst is True:
            self.headrow = self.datalist.pop(0)
        else:
            self.headrow = headrow
        self.workfd = self.__class__.workfd or os.getcwd()

    def _serial(self, datastream):
        # datalist is string => list of list
        cell_split = '\t'
        row_split = '\n'
        rows = datastream.split(row_split)
        datalist = []
        for r in rows:
            datalist.append(r.split(cell_split))
        return datalist

    def _checkfile(self, filename):
        p = filename.rfind('.')
        if p > 0:
            fnbody = filename[:p]
            fnext = filename[p:]
        else:
            fnbody = filename
            fnext = ''
        while True:
            fpth = os.path.join(self.workfd, fnbody + fnext)
            if os.path.exists(fpth):
                fpth = fnbody + '_' + str(time.time()).replace('.', '_')
            else:
                break
        return fnbody + fnext

    def _xls_copy(self, fromfile, newfile):
        # copy template xls file to a new one
        if not fromfile.endswith('xls'):
            fromfile = fromfile + '.xls'
        if not newfile.endswith('xls'):
            newfile = newfile + '.xls'
        if fromfile == newfile:
            raise ValueError("fromfile == newfile")
        fromfile = os.path.join(self.workfd, fromfile)
        newfile = os.path.join(self.workfd, newfile)
        shutil.copyfile(fromfile, newfile)

    def from_tpl(self, template, values, filename=None):
        # template: template name:
        # [[key, row, col]] => key => datastream: {key:value, key:value...}
        tpler = xltpl(template).export()
        filename = (filename or str(uuid.uuid1())) + '.xls'
        self._xls_copy(template, filename)
        wbook = xlwt.Workbook(encoding='utf-8')
        worksheet = wbook.add_sheet('sheet1')
        for key,r,c in tpler:
            v = values.get(key)
            if v:
                worksheet.write(r, c, v)
        wbook.save()

    def exp_xls(self, filename=''):
        filename = (filename or str(uuid.uuid1())) + '.xls'
        filename = self._checkfile(filename)
        filepath = os.path.join(self.workfd, filename)
        wbook = xlwt.Workbook(encoding='utf-8')
        worksheet = wbook.add_sheet(u'成绩表')
        rowid = 0
        cellid = 0
        for row in self.datalist:
            for cell in row:
                worksheet.write(rowid, cellid, cell)
                cellid += 1
            cellid = 0
            rowid += 1
        wbook.save(filepath)
        self.xls = filename
        return filepath

    def exp_csv(self, filename=''):
        filename = (filename or str(uuid.uuid1())) + '.csv'
        filename = self._checkfile(filename)
        filepath = os.path.join(self.workfd, filename)
        with open(filepath, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for row in self.datalist:
                writer.writerow([s.encode('utf-8') for s in row])
        self.csv = filename
        return filepath


if __name__ == '__main__':
    xltpl.workfd = 'd:\\tmps'
    #xltpl.gen_by_xls('ny_cal.xls')
    print xltpl('ny_cal').export()