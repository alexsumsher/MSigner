#!/usr/bin/env python
# -*- coding: utf8
# 
import os
import cStringIO
import re
import codecs

#   Text Mixer unicode
def sMixer(fd, file_list, codec=''):
    fd = fd or os.getcwd()
    steam = cStringIO.StringIO()
    for f in file_list:
        fp = os.path.join(fd, f)
        if os.path.exists(fp):
            try:
                ff = open(fp, 'rb')
                fs = ff.read()
            except IOError:
                return ''
            finally:
                ff.close()
            steam.write(fs)
        else:
            return ''
    steam.seek(0)
    if codec:
        return codecs.decode(steam.read(), codec)
    else:
        return steam.read()

def eMixer(source_file, parts_folder, codec='', basedir='', **sparts):
    # choose part file from parts_folder and embed to source_file where marked by segment-name
    # html文件拼合
    def load_part(fp):
        if os.path.exists(fp):
            f = open(fp, 'rb')
            fd = f.read()
            f.close()
            return fd
        else:
            return None
    re_mark = re.compile(r'\{\{([F|S])?segment\:\s([\w\.\_]+)|endseg\}\}')
    if basedir:
        source_file = os.path.join(basedir, source_file)
        parts_folder = os.path.join(basedir, parts_folder)
    print source_file,parts_folder
    assert os.path.exists(source_file) and os.path.isdir(parts_folder)
    steam = cStringIO.StringIO()
    with open(source_file, 'rb') as sf:
        for line in sf:
            if line.startswith('{{'):
                try:
                    parttype,partname = re_mark.search(line).groups()
                except AttributeError:
                    #steam.write(line)
                    continue
                if parttype == 'F':
                    partdata = load_part(os.path.join(parts_folder, partname))
                elif parttype == 'S':
                    partdata = sparts.get(partname)
                if partdata:
                    steam.write('\n')
                    steam.write(partdata)
            else:
                steam.write(line)
    steam.seek(0)
    #   for l in steam:\n\tprint codecs.decode(l, 'utf8')
    return steam

class sCache:
    def __init__(self, size):
        self.cache = {}
        self.countor = Counter()
        self.size = size

    def __getitem__(self, sname, data=None):
        self.countor[sname] += 1
        if data:
            return self.put(sname, data)
        else:
            return self.cache.get(sname)

    def put(self, sname, data):
        if self.size > len(self.cache):
            self.cache[sname] = data
        else:
            k,v = self.countor.most_common()[self.size-1]
            if self.countor[sname] > v:
                self.cache.pop(k)
                self.cache[sname] = data
        return data

    def reset(self, size=5):
        self.size = size
        self.countor.clear()
        self.countor.update(self.cache.keys())

#   get segment(s) streamfrom a segment file
#   file structure: {segment: segment_name}segment text{endseg}, no embed
#   end of file(fixed):{segname: [linestart,lineend], ...}
class fMixer(object):
    re_mark = re.compile(r'\{\{(segment\:\s(\w+)|endseg)\}\}')

    @classmethod
    def ini_mixer(cls, folder, size=6, force=False):
        if hasattr(cls, folder) and not force:
            raise ValueError('fMixer has been initialized!')
        if os.path.exists(folder):
            cls.folder = folder
        cls.size = size
        cls.lrcache = sCache(cls.size)

    @classmethod
    def reset(cls, size=6):
        self.lrcache.reset(size=size)

    
    def __init__(self, segfile):
        path = os.path.join(fMixer.folder, segfile)
        assert os.path.exists(path)
        self.filepath = path
        self.segfile = segfile
        self.segments = {}

    def __getitem__(self, segname=''):
        if segname:
            return self.load_seg(segname)
        else:
            self.load_segfile()
            return self.segments

    def load_segfile(self, update=False):
        with open(self.segfile, 'r+') as sf:
            linedata = sf.readlines()
            lsl = linedata[-1]
            if lsl.startswith('{\''):
                if update:
                    linedata.pop()
                    self.segments.clear()
                    self._mark_lines(linedata)
                else:
                    self.segments = eval(lsl)
            else:
                self._mark_lines(linedata)
            if self.segments:
                sf.seek(0,2)
                sf.write('\n')
                sf.write(str(self.segments))
        if self.segments:
            return True
        return False

    def load_seg(self, segname, force=False):
        longname = self.segfile + '-' + segname
        data = fMixer.lrcache[longname]
        if not force and data:
            return data
        if not self.segments and not self.load_segfile():
            raise ValueError('NO SEGMENT informations Found in file:\n%s' % self.filepath)
        if segname in self.segments:
            st,ed = self.segments[segname]
            with open(self.filepath, 'r') as sf:
                for x in xrange(st):
                    sf.readline()
                data = ''
                for x in xrange(ed - st -1):
                    data += sf.readline()
            # data = codecs.decode(data, 'utf8')
            fMixer.lrcache.put(longname, data)
            return data
        else:
            return None

    def load_segs(self, segnames, force=False):
        if isinstance(segnames, str):
            return self.load_seg(segnames, force=force)
        segs = []
        segs.extend(segnames)
        collect_data = cStringIO.StringIO()
        line_places = []
        for seg in segs:
            longname = self.segfile + '-' + seg
            if fMixer.lrcache[longname]:
                collect_data.write(fMixer.lrcache[longname])
            elif seg in self.segments:
                line_places.extend(self.segments[seg])
        line_places.sort()
        with open(self.filepath, 'r') as sf:
            pre_st = 0
            pre_ed = 0
            for x in xrange(len(line_places) // 2):
                st = line_places[x] - pre_st
                ed = line_places[x+1] - pre_ed
                for p in xrange(st):
                    sf.readline()
                for p in xrange(ed - st - 1):
                    collect_data.write(sf.readline())
                pre_st = st
                pre_ed = ed
        collect_data.seek(0)
        return collect_data.read()

    def _mark_lines(self, linesdata, startline=0):
        inseg = 0
        segname = ''
        linecount = startline
        for line in linesdata:
            linecount += 1
            if line[:2] == '{{':
                try:
                    act = fMixer.re_mark.match(line).groups()
                except AttributeError:
                    continue
                if act[1] and inseg == 0:
                    segname = act[1]
                    self.segments[segname] = [linecount]
                    inseg = 1
                    continue
                if act[0] == 'endseg' and inseg == 1:
                    self.segments[segname].append(linecount)
                    inseg = 0
                    continue