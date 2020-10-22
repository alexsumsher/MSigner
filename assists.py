import time
import random
import string
from flask import make_response
import json
from modules import user_tbl as UTBL


def code_gender(length=12, only_char=False, asc_case=0, only_number=False, symbols=False):
	if only_char:
		if asc_case == 1:
			cset = string.ascii_lowercase
		elif asc_case == 2:
			cset = string.ascii_uppercase
		else:
			cset = string.ascii_letters
	elif only_number:
		cset = string.digits
	else:
		cset = string.ascii_letters + string.digits
	if symbols is True:
		# cset += string.punctuation
		cset += '+-_=&!'
	return ''.join(random.choices(cset, k=length))


def cookie_file_respon(file_input, cookies):
    #   make sure that: values must be STRING
    if isinstance(file_input, str):
        fo = open(file_input, 'rb')
    elif hasattr(file_input, 'seek'):
        fo = file_input
    else:
        raise ValueError("not a correct filepath/fileobject!")
    data = fo.read()
    rsp = make_response(data)
    fo.close()
    for k,v in cookies.items():
        rsp.set_cookie(k, value=v if isinstance(v, str) else str(v))
    return rsp

def plus_file_respon(file_input, env_values):
    # 直接插入<script>const serverdata={}</script>
    # 放置在</body>\r\n之后
    if isinstance(file_input, str):
        fo = open(file_input, 'rb')
    elif hasattr(file_input, 'seek'):
        fo = file_input
    else:
        raise ValueError("not a correct filepath/fileobject!")
    fdata = fo.read()
    script_string = b'</body>\r\n<script language="javascript">\r\nconst serverdata=%s</script>' % json.dumps(env_values).encode()
    return fdata.replace(b'</body>\r\n', script_string)

def wxlogin(userid, password, openid=None):
	udata = UTBL.user_by_userid(userid)
	if openid and udata['openid'] != openid:
		return False
	if udata['password'] == password:
		return True
	else:
		return False