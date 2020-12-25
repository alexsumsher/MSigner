// login
_env = {
	browser: null,
	cookiedays: 10,
	md5len: 32,
}
const get_json = function(dlg, item_names, item_mode, sp_ids, fillvals, skip_space){
	// skip_space: if value is set to ""; ignore
	// data-value: 优先于value；通常展示为用户可读，但实际需要值是编号;主要用于text
	const gv = function(ipt){
		let _v;
		switch(ipt.type){
			case "text": _v = ipt.dataset.value || ipt.value;break;
			case "select-multiple": {
				let vlist = [];
				let sos = ipt.selectedOptions;
				for(let i=0,len=sos.length;i<len;i++){
					vlist.push(sos[i].dataset.value || sos[i].value);
				};
				_v = vlist.join(',');
			};break;
			//case "select-one":ipt.options[ipt.selectedIndex].value;
			case "radio": if(ipt.checked){_v = ipt.value};break;
			case "checkbox": if(ipt.checked){_v = ipt.value};break;
			default: _v = ipt.dataset.value || ipt.value;
		}
		return _v;
	}
	
	let tform = document.querySelector(dlg);
	if (!tform){
		return null;
	}
	var rta = {};
	var imode = 0;//0:default;1:item_name to collect;2:item_name to remove
	if(item_names instanceof Array && item_mode !== '-'){
		for(var i=0,len=item_names;i<len;i++){
			rta[item_names[i]] = null;
		}
		imode = 1;
	}else{
		tform.querySelectorAll('[name]').forEach((itm)=>{
			let name = itm.getAttribute('name');
			if(imode === 1 && rta[name] !== null){
			  // if imode===1, rta[name] should have been set to null,
			  // so when rta[name] !== null, it's no need to collect
			  return;
			}
			if(itm.nodeName === 'DIV'){
				let thisvar = [];
				itm.querySelectorAll('input').forEach((n)=>{
					var v = gv(n);
					if(v === '' && skip_space){
						//pass
					}else{
						thisvar.push(v);
					}
				});
				// not a input item, use getattribute mode
				if(thisvar.length>0){
					rta[name] = thisvar;
				}else if(skip_space){
					//pass
				}else{
					rta[name] = typeof(fillvals)==="object"?fillvals[name]:'';
				}
				return;
			}
			var v = gv(itm);
			if (rta[name]){
				//pass when already have value with the same name(avoiding Conflict)
			}else if(v){
				rta[name] = v || fillvals || fillvals[name];
			}
		});
		// if there is some item don't wannt to post
		if(item_names instanceof Array && item_mode === '-'){
			for(var i=0,len=item_names.length;i<len;i++){
				delete rta[item_names[i]];
			}
		}
	}
	//special target withou a [name] attribute
	if(sp_ids){
		var tv;
		[].concat(sp_ids).map(function(v, i){
			tv = tform.querySelector('#' + v).text();
			if(tv){rta[v] = tv}
		});
	}
	return rta;
}

const cookies = function(vname, value, expires){
	// expires = day
	if(typeof(vname) !== 'string'){
		return null;
	}
	if(value === undefined){
		//get value from cookie
		//var cukyRE = new RegExp('(;|^)' + vname + '=(.*)?;{0,1}');
		var cukyRE = new RegExp('\s{0,1}' + vname + '\=(.*?)(\;|$)');
		try{
		return cukyRE.exec(document.cookie)[1];
		}catch(e){
		return null;
		}
	}

	let ending = ";";
	
	if (expires){
		var exdate = new Date();
		exdate.setTime(exdate.getTime() + (expires*24*60*60*1000));
		ending = ';expires=' + exdate.toUTCString() + ';';
	}
	let cs = vname + '=' + escape(value) + ending + "path=/";
	console.log(cs);
	document.cookie = cs;
	//document.cookie = 'expires=' + exdate.toGMTString();
	return vname;
}

function myBrowser() {
    var userAgent = navigator.userAgent; //取得浏览器的userAgent字符串
    var isOpera = userAgent.indexOf("Opera") > -1; //判断是否Opera浏览器
    var isIE = userAgent.indexOf("compatible") > -1
            && userAgent.indexOf("MSIE") > -1 && !isOpera; //判断是否IE浏览器
    var isEdge = userAgent.indexOf("Edge") > -1; //判断是否IE的Edge浏览器
    var isFF = userAgent.indexOf("Firefox") > -1; //判断是否Firefox浏览器
    var isSafari = userAgent.indexOf("Safari") > -1
            && userAgent.indexOf("Chrome") == -1; //判断是否Safari浏览器
    var isChrome = userAgent.indexOf("Chrome") > -1
            && userAgent.indexOf("Safari") > -1; //判断Chrome浏览器

    if (isIE) {
        var reIE = new RegExp("MSIE (\\d+\\.\\d+);");
        reIE.test(userAgent);
        var fIEVersion = parseFloat(RegExp["$1"]);
        if (fIEVersion == 7) {
            return "IE7";
        } else if (fIEVersion == 8) {
            return "IE8";
        } else if (fIEVersion == 9) {
            return "IE9";
        } else if (fIEVersion == 10) {
            return "IE10";
        } else if (fIEVersion == 11) {
            return "IE11";
        } else {
            return "0";
        }//IE版本过低
        return "IE";
    }
    if (isOpera) {
        return "Opera";
    }
    if (isEdge) {
        return "Edge";
    }
    if (isFF) {
        return "FF";
    }
    if (isSafari) {
        return "Safari";
    }
    if (isChrome) {
        return "Chrome";
    }
}


page_initor('login-page', function(){});


_PGC.bind_ini("login-page", function(){
	
	let _this = document.getElementById(_PGC.cur_page);
	let org_seler = _this.querySelector("#organization");
	$.getJSON("/resource/school", {action: 'list', as_option: 'yes'}, function(rsp){
		if (rsp && rsp.success === 'yes'){
			_exec.set_sel_opts_ex(org_seler, rsp.data);
		}
	});
	
	document.getElementById("go_login").addEventListener("click", function(evt){
		//pass
		let params = get_json("#dlg_login");
		params['objid'] = org_seler.value;
		$.post("/login?action=login", params, function(rsp){
			console.log(rsp);
			if (rsp.success === 'yes'){
				// special path
				if (rsp.data.startsWith("/")){
					window.location.href = rsp.data;
					return;
				}
				// normal
				let tgl_autopwd = document.getElementById("tgl_autopwd");
				sessionStorage["objid"] = params.objid;
				sessionStorage["userid"] = rsp.data;
				sessionStorage["orgtype"] = "organize";
				if (tgl_autopwd.checked){
					// 保存本地密码
					// update: 如果有账号且正常登陆则保存账号+密码，否则保存项目名称+密码					
					cookies('mypwd', params.password, _env.cookiedays);
					cookies('myobjid', params.objid, _env.cookiedays);
					cookies('username', params.username, _env.cookiedays);
				}
				userid = rsp.data;
				window.location.href = "/index?objectid=" + params.objid + "&userid=" + userid;
			}else {
				alert("错误: " + rsp.msg);
			}
		}, 'json');
	});
});

_PGC.bind_ini("regist-page", function(){
	// set options
	let _this = document.getElementById(_PGC.cur_page);
	let org_seler = _this.querySelector("#organization");
	$.getJSON("/resource/school", {action: 'list', as_option: 'yes'}, function(rsp){
		if (rsp && rsp.success === 'yes'){
			_exec.set_sel_opts_ex(org_seler, rsp.data);
		}
	});
	
	_this.querySelector("#go_regist").addEventListener("click", function(evt){
		let params = get_json("#dlg_regist");
		params['objid'] = org_seler.value;
		$.post("/login?action=regist", params, function(rsp){
			console.log(rsp);
			if (rsp.success === 'yes'){
				sessionStorage["userid"] = rsp.data;
				alert("注册OK");
				go_page("login-page");
				//window.location.href = "/index&objectid=" + myobjid + "&userid=" + userid;
			}else {
				alert("错误: " + rsp.msg);
			}
		}, 'json');
	});
});




$(document).ready(function() {
	//document.getElementById("capimg").click();
	_env.browser = myBrowser();
	if (_env.browser !== 'Chrome'){
		alert('您使用的不是谷歌浏览器，强烈建议使用谷歌浏览器！\n否则可能无法正常使用系统。\n如果是360等浏览器，请使用“急速模式”!');
	}
	// 清除SS
	sessionStorage['muser'] = "";
	// 填充密码
	let pwd = cookies('mypwd');
	let _loginw = document.getElementById("login-page");
	if (pwd){
		_loginw.querySelector('[name="password"]').value = pwd;
		let tgl_autopwd = document.getElementById("tgl_autopwd");
		tgl_autopwd.checked = true;
	}
	let acc = cookies('username');
	if (acc){
		_loginw.querySelector('[name="account"]').value = acc;
	}
	let org = cookies('myobjid');
	if (org){
		_loginw.querySelector("#organization").value = org;
	}
});