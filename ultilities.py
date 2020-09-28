#!/usr/bin/env python
# -*- coding: utf8
# 
import re
import urllib
import os
# 
def geturl_2_dict_and_list(request_data_string):
    # scores%5b0%5d%5buser_no%5d%3d002%26scores%5b0%5d%5bscore%5d%3d78%26scores%5b0%5d%5bremark%5d%3d%26scores%5b1%5d%5buser_no%5d%3d003%26scores%5b1%5d%5bscore%5d%3d79%26scores%5b1%5d%5bremark%5d%3d%26scores%5b2%5d%5buser_no%5d%3d004%26scores%5b2%5d%5bscore%5d%3d80%26scores%5b2%5d%5bremark%5d%3d%26scores%5b3%5d%5buser_no%5d%3d005%26scores%5b3%5d%5bscore%5d%3d89%26scores%5b3%5d%5bremark%5d%3d%26xdatas%5b0%5d%5buser_no%5d%3d002%26xdatas%5b0%5d%5bscore%5d%3d78%26xdatas%5b0%5d%5bremark%5d%3d%26xdatas%5b1%5d%5buser_no%5d%3d003%26xdatas%5b1%5d%5bscore%5d%3d79%26xdatas%5b1%5d%5bremark%5d%3d%26xdatas%5b2%5d%5buser_no%5d%3d004%26xdatas%5b2%5d%5bscore%5d%3d80%26xdatas%5b2%5d%5bremark%5d%3d%26xdatas%5b3%5d%5buser_no%5d%3d005%26xdatas%5b3%5d%5bscore%5d%3d89%26xdatas%5b3%5d%5bremark%5d%3d%26target%3d%26target%3dclass%26yearid%3dAyA0hzjuneQNZAdone%26termid%3dxmasx7Xgk3OiqQdone%26classid%3d3B22rlgGQz8done%26gradeid%3dzAoYvY2Z14Edone%26subjectid%3dErOFkIllCSIdone => 
    # {'classid': '3B22rlgGQz8done', 'target': 'class', 'gradeid': 'zAoYvY2Z14Edone', 'subjectid': 'ErOFkIllCSIdone', 'yearid': 'AyA0hzjuneQNZAdone', 'termid': 'xmasx7Xgk3OiqQdone', 'scores': [{'remark': '', 'score': '78', 'user_no': '002'}, {'remark': '', 'score': '79', 'user_no': '003'}, {'remark': '', 'score': '80', 'user_no': '004'}, {'remark': '', 'score': '89', 'user_no': '005'}], 'xdatas': [{'remark': '', 'score': '78', 'user_no': '002'}, {'remark': '', 'score': '79', 'user_no': '003'}, {'remark': '', 'score': '80', 'user_no': '004'}, {'remark': '', 'score': '89', 'user_no': '005'}]}
    # export get request string(urlencoded) to dict with list (when level 2 is integer)
    outdict = {}
    subkeys = set()
    idx = 0
    rdss = re.split(r'[\=|\&]', urllib.unquote(request_data_string))
    ree = re.compile(r'\[([\w|_|-]+)\]')
    for x in range(len(rdss)/2):
        key = rdss[x * 2]
        val = rdss[x * 2 + 1]
        m = ree.findall(key)
        if len(m) == 0:
            outdict[key] = val
            continue
        #print m
        curkey = key[:key.index('[')]
        if m[0].isdigit():
            idx = int(m[0])
            if curkey not in subkeys:
                outdict[curkey] = []
                subkeys.add(curkey)
            node = outdict[curkey]
            delta = idx - len(node)
            if delta >= 1:
                node.extend([None]*(delta + 1))
                node[idx] = dict()
            elif delta == 0:
                node.append(dict())
            if node[idx] is None:
                node[idx] = dict()
            node = node[idx]
            m.pop(0)
        else:
            if curkey not in outdict:
                outdict[curkey] = dict()
            node = outdict[curkey]
        for x in range(len(m)):
            k = m.pop(0)
            if len(m) == 0:
                node[k] = val
                break
            if k not in node:
                node[k] = dict()
            node = node[k]
    return outdict
# 
def json_flat_2_tree(reqfm):
    #parse a reqest.form:
    # {'a':1,'b':2,'c[a]':11,'c[b]':22,'c[c][a]':111,'c[c][b]':222}
    # => {'a': 1, 'c': {'a': 11, 'c': {'a': 111, 'b': 222}, 'b': 22}, 'b': 2}
    ree = re.compile(r'\[([\w|_|-]+)\]')
    outdict = {}
    for key,val in reqfm.items():
        m = ree.findall(key)
        if len(m) == 0:
            outdict[key] = val
        else:
            curkey = key[:key.index('[')]
            if curkey not in outdict:
                outdict[curkey] = dict()
            t = outdict[curkey]
            for x in range(len(m)):
                k = m.pop(0)
                if len(m) == 0:
                    t[k] = val
                    break
                if k not in t:
                    t[k] = dict()
                t = t[k]
    return outdict

def json_flat_2_list(reqfm):
    # module: {'classid': u'3B22rlgGQz8done', 'scores[3][remark]': u'', 'scores[2][remark]': u'', 'scores[0][score]': u'78', 'scores[0][remark]': u'', 'scores[1][user_no]': u'003', 'gradeid': u'zAoYvY2Z14Edone', 'subjectid': u'ErOFkIllCSIdone', 'scores[0][user_no]': u'002', 'yearid': u'AyA0hzjuneQNZAdone', 'termid': u'xmasx7Xgk3OiqQdone', 'scores[1][remark]': u'', 'scores[2][score]': u'80', 'scores[3][score]': u'89', 'scores[1][score]': u'79', 'scores[3][user_no]': u'005', 'scores[2][user_no]': u'004', 'target': u'class'}
    # => score list: work 2 level now
    ree = re.compile(r'\[([\w|_|-]+)\]')
    outdict = {}
    subkeys = set()
    idx = 0
    for key,val in reqfm.items():
        m = ree.findall(key)
        if len(m) == 0:
            outdict[key] = val
            continue
        #print m
        curkey = key[:key.index('[')]
        if m[0].isdigit():
            idx = int(m[0])
            if curkey not in subkeys:
                outdict[curkey] = []
                subkeys.add(curkey)
            node = outdict[curkey]
            delta = idx - len(node)
            if delta >= 1:
                node.extend([None]*(delta + 1))
                node[idx] = dict()
            elif delta == 0:
                node.append(dict())
            if node[idx] is None:
                node[idx] = dict()
            node = node[idx]
            m.pop(0)
        else:
            if curkey not in outdict:
                outdict[curkey] = dict()
            node = outdict[curkey]
        for x in range(len(m)):
            k = m.pop(0)
            if len(m) == 0:
                node[k] = val
                break
            if k not in node:
                node[k] = dict()
            node = node[k]
    return outdict

def dict2url(in_dict, encode=True):
    #parse post data into 'key[subkey]=value&...' pattern
    #the correct way for postdata
    curkey = ''
    cpos = 0
    workd = dict()
    def seperate(curkey, cpos, ind):
        for k,v in ind.items():
            if isinstance(v, dict):
                cpos += 1
                curkey += '[%s]' % k if cpos > 1 else k
                seperate(curkey, cpos, v)
            else:
                if cpos > 0:
                    workd[curkey + '[%s]' % k] = v
                else:
                    workd[k] = v
        cpos -= 1
        curkey = curkey[:curkey.rindex('[')] if cpos > 1 else curkey
    seperate(curkey, cpos, in_dict)
    ostr = '&'.join(['%s=%s' % (k, workd[k]) for k in workd.keys()])
    if encode:
        return ostr.encode('utf8') if isinstance(ostr, unicode) else ostr.decode('gbk').encode('utf8')
    else:
        return ostr

def json2dict(jsonstr):
    # '{"a":1,"b":{"a": {"a": 111, "b": 222}, "b":22}, "c":3}' => dict
    # 1) ['{"a"', 1, '"b"', '{"a"', '{"a"', '"b"', '222}', '"b"', '22}', '"c"', '3}']
    # 2) pop(0), d=dict(), d['a'] = ?, startswith('{') then d['a']=dict() else d['a'] = ?, ...
    # from unicode
    pairs = re.split(r'[\,\s+\"|\"\:]', jsonstr)
    outd = dict()
    pairs.pop(0) # pop first '{'
    curkey = None
    d_list = [outd]
    curd = outd
    for x in pairs:
        if len(x) == 0:
            continue
        if curkey is None:
            curkey = x
            continue
        if x == '{':
            curd = d_list[-1]
            curd[curkey] = dict()
            curd = curd[curkey]
            d_list.append(curd)
            curkey = None
        elif x.endswith('}'):
            curd = d_list.pop(-1)
            curd[curkey] = x[:-1]
            curkey = None
        else:
            curd[curkey] = x
            curkey = None
    return outd


# find some key-value from dict and export dict with find keys
# function-1: key_from_tree => small size, one key one big loop
# function-2: filter_dict => big size, flatenning dict to find
# {a: va, b: {b-a: vb-a, b-b: {b-b-a: vb-b-a}, b-c: vb-c}, c: vc} =>
# {a: va, b-a: vb-a, b-b-a: vb-b-a, b-c: vb-c, c: vc}
def key_from_tree(key, fromdict):
    # recursive
    iter_dicts = fromdict.items()
    while iter_dicts:
        k, v = iter_dicts.pop(0)
        if isinstance(v, dict):
            iter_dicts.extend(v.items())
        elif key == k:
            return v

def filter_dict(keys, dict_in, dict_out):
        if not isinstance(dict_out, dict):
            dict_out = dict()
        if len(keys) < 6:
            # if > 10 flat the dict_in to dict_tmp
            # here require key_from_tree
            for key in keys:
                dict_out[key] = key_from_tree(key, dict_in)
            return dict_out
        dict_tmp = dict()
        dict_tmp.update(dict_in.items())
        def flat_dict_for_key(fk):
            if fk in dict_tmp:
                v = dict_tmp.pop(fk)
                if isinstance(v, dict):
                    raise RuntimeError("key for dictionary!")
                return v
            #print dict_tmp
            flats = 0
            for k,v in dict_tmp.items():
                if isinstance(v, dict):
                    dict_tmp.pop(k)
                    dict_tmp.update(v.items())
                    flats += 1
            if flats > 0:
                return flat_dict_for_key(fk)
            else:
                return None
        for key in keys:
            val = flat_dict_for_key(key)
            if val is None:
                raise RuntimeError("not found with: %s" % key)
            dict_out[key] = val
        return dict_out

def filter_json(keys, jsonstr, def_dict=None):
    # filter key:value for keys to a new dictionary
    dict_out = dict.fromkeys(keys) if def_dict is None else def_dict
    segs = re.split(r',\s*\"', jsonstr)
    for seg in segs:
        seg = seg.replace('"','')
        try:
            # if 0 should be 1
            stp = seg.index('{') or 1
        except ValueError:
            stp = 0
        mtp = seg.index(':')
        rkey = seg[stp:mtp]
        if rkey in dict_out:
            etp = -1 if seg.endswith('}') else None
            rval = seg[mtp:etp].strip()
            if rval is None:
                raise ValueError("key: %s not found!" % rkey)
            else:
                dict_out[rkey] = rval
    return dict_out

def dict_search(dictin, keyname, keyvalue, one=False):
    # recursion deep search dict for each dict that have keyname=keyvalue
    # one: the first one with keyname will be ok;
    collection = []
    def deepdict(d):
        if len(collection) >= 1:
            return
        for k in d:
            if isinstance(k, (list, dict)):
                deepdict(k)
                continue
            v = d[k]
            if k == keyname and v == keyvalue:
                collection.append(d)
                return
            elif isinstance(v, (list, dict)):
                deepdict(v)
                continue
    deepdict(dictin)
    return collection[0] if one else collection

def dict_search2(dictin, keyname, keyvalue, one=False):
    # Iterative 
    collection = [dictin]
    outs = []
    max = 3000
    for x in range(max):
        if len(collection) > 0:
            i = collection.pop(0)
        else:
            return outs
        if isinstance(i, list):
            collection.extend(i)
            continue
        elif isinstance(i, dict):
            for k,v in i.items():
                if isinstance(v, dict):
                    collection.append(v)
                elif isinstance(v, list):
                    collection.extend(v)
                elif k == keyname and v == keyvalue:
                    if one is True:
                        return i
                    outs.append(i)
                    break
    return outs

def dict_search3(dictin, keyname, keyvalues, one=False, listout=True, outkey='departid'):
    # Iterative 从DICT遍历所有的子dict获取keyname=keyvalue的dict
    # 如果以dict输出，outkey为指定的输出dict的key名称（subdict必须包含)
    if isinstance(keyvalues, (list,tuple)):
        checker = lambda s: s in keyvalues
    else:
        checker = lambda s: s == keyvalues
    collection = [dictin]
    outs = [] if listout else {}
    max = 3000
    for x in range(max):
        if len(collection) > 0:
            i = collection.pop(0)
        else:
            return outs
        if isinstance(i, list):
            collection.extend(i)
            continue
        elif isinstance(i, dict):
            for k,v in i.items():
                if isinstance(v, dict):
                    collection.append(v)
                elif isinstance(v, list):
                    collection.extend(v)
                elif k == keyname and checker(v):
                    if one is True:
                        return i
                    if listout:
                        outs.append(i)
                    else:
                        outs[i[outkey]] = i
                    break
    return outs

def req_filter(req, gets=None, nonull=True):
    if gets:
        outs = dict.fromkeys(gets if isinstance(gets, (list, tuple)) else gets.split(','))
        for k in outs.keys():
            if req[k] and req[k] != 'null':
                outs[k] = req[k]
            else:
                outs[k] = None
    else:
        outs = req.to_dict()
        if nonull:
            for k in outs.keys():
                if outs[k] == 'null':
                    outs[k] = None
    return outs


#   do the zip actions
def zipdir(target, zipdir, zipfilename='pnoutzip'):
    import zipfile
    if not os.path.exists(target):
        print('not found target dir: %s' % target)
        return ''
    if not os.path.exists(zipdir):
        print('not found target dir: %s' % zipdir)
        return ''
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except ImportError:
        compression = zipfile.ZIP_STORED
    predir = os.getcwd()
    os.chdir(zipdir)
    zipfilename = zipfilename if zipfilename.rfind('.zip') > 0 else zipfilename + '.zip'
    if os.path.exists(zipfilename):
        zipfilename = zipfilename[:-4] + ut_timestampname(ext='zip')
    z = zipfile.ZipFile(zipfilename, mode="w", compression=compression)
    if os.path.isdir(target):
        start = target.rfind(os.sep) + 1
        for f in os.listdir(target):
            fpath = os.path.join(target, f)
            z.write(fpath, fpath[start:])
    else:
        #   save without a path
        z.write(target, os.path.basename(target))
    z.close()
    if os.path.exists(predir):
        os.chdir(predir)
    return zipfilename


def unzipfile(zipfilepath, updir):
    import zipfile
    fcount = 0
    unzipdir = os.path.join(updir, 'unzipdir')
    if zipfile.is_zipfile(zipfilepath):
        f2uzip = zipfile.ZipFile(zipfilepath, 'r')
        for f in f2uzip.namelist():
            print(f)
            fcount += 1
            try:
                f2uzip.extract(f, unzipdir)
            except RuntimeError as e:
                print(e)
                return 'unzip error', 0
    else:
        print('not a zip file.')
        return 0
    return unzipdir, fcount


def check_client(useragent):
    if not useragent:
        return 'mobile'
    useragent = useragent.lower()
    if useragent.find('mobile') > 0:
        return 'mobile'
    elif useragent.find('micromessenger') > 0:
        return 'wx'
    else:
        return 'pc'

if __name__ == '__main__':
    #tstr = u'{"a": "你好","b":{"aa": {"aaa": "性别:男,年龄:22", "bbb": 222}, "bb":22}, "c":3}'
    # re.split(r',\s*\"',tstr)
    # [u'{"a": "\u4f60\u597d"', u'b":{"aa": {"aaa": "\u6027\u522b:\u7537,\u5e74\u9f84:22"', u'bbb": 222}', u'bb":22}', u'c":3}']
    #print filter_json(('bbb', 'bb', 'a'), tstr)
    pass