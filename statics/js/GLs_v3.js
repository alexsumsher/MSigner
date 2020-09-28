//GLS v2
// ES6
// ZUI.1.81
// Work for loankeeper with some special defination
String.prototype.Join = function(str_list){
	// 'abc'.Join(['a', 'b', 'c']) => aabcbabcc
	if(str_list instanceof Array){
		var rts = '';
		for (var i=0,len=str_list.length;i<len-1;i++){
			rts += (String(str_list[i]) + this);
		}
		rts += String(str_list[i]);
		return rts
	}else{
		return ''
	}
}

function dout(tip, msg){
	if(msg === undefined || msg === null){
    console.log('DOUT: ' + tip + ': ...');
    return;
	}else if(typeof(msg) === 'object' && msg.constructor.prototype === msg.__proto__){
		console.log(tip + ':\t' + JSON.stringify(msg));
    return;
	}else{
    console.log(tip + ': ' + msg || string(msg));
    return;
	}
}

function Jsession(arg, setname){
	// if strin is set to plain object; update sessionStorage items and JSnames
	// if setrin not set 
	setname = setname || "__JSnames"
	let S = window.sessionStorage,
		vars = null,
		out = null;
	let olds = S.getItem(setname);
	if(!olds){
		S.setItem(setname, "_version");
		S.setItem("_version", 0);
		vars = [];
	}else{
		vars = olds.split(",");
	}
	if(!arg){
		out = {};
		vars.forEach((n)=>{
			out[n] = S.getItem(n) || "";
		});
	}else if(typeof(arg) === 'object'){
		// update
		for(let n in arg){
			S.setItem(n, String(arg[n]));
			if(vars.indexOf(n)<0){
				olds += "," + n;
			}
		}
		S.setItem("setname", olds);
		out = olds;
	}else if(typeof(arg) === 'string'){
		return S.getItem(arg);
	}
	return out;
}

window._exec = {
  get_urlparam: function(param, url, outmode){
		if (param === '' || param == null){
			//consider for filter block:
			var params = url.split(/[\?|\&|\=]/g);
			if(params.length > 1 && params.length % 2 === 1){
				var outs;
				if(outmode === 'list'){
					outs = params.slice(1);
				}else{
					outs = {};
					for(let i=1;i<params.length;i+=2){
						outs[params[i]] = params[i+1];
					}
				}
				return outs;
			}else{
				return null;
			}
		}else{
			var getter = new RegExp('[\?\&]' + param + '=(.*?)($|\&)');
			var rt = getter.exec(url);
			if (rt){
				return rt[1];
			}else{
				return undefined;
			}
		}
	},
  
  make_urlparam: function(paramobj, baseurl, esc){
    //paramlist: {param:value, param:value}; if remove param, use like: {param: null}
    if (!paramobj){
      return baseurl;
    }
    var url = typeof(baseurl) === 'string'?baseurl:location.href;
    if (url.substr(-1) !== '?'){
      if (url.indexOf('?') < 0){
        url += '?';
      }else{
        url += '&';
      }
    }
    var p='';
    if ($.isPlainObject(paramobj)){
      // {param1: value1, param2: value2...}
      for(var param in paramobj){
        p = esc?(paramobj[param] === null?null:escape(paramobj[param])):paramobj[param];
        if (p === ''){
          continue;
        }else if(p === null){
          var getter = RegExp('[\\?\\&]' + param + '=\\w+');
          url = url.replace(getter, '');
				}else if (url.search('[\\?\\&]' + param + '\\=') < 0){
          url += (param + '=' + p + '&');
        }else{
          var getter = RegExp('(?![\\?\\&])' + param + '=\\w+');
          url = url.replace(getter, param + '=' + p);
        }
      }
    }else if ($.isArray(paramobj)){
      // [param1, value1, param2, value2...]
      for(var i=0, len=paramobj.length; i<len; i=i+2){
        p = esc?(paramobj[i+1] === null?null:escape(paramobj[i+1])):paramobj[i+1];
        if (p === ''){
          continue;
        }else if (url.indexOf(paramobj[i] + '=') < 0 && p !== null){
          url = url + paramobj[i] + '=' + p + '&';
        }else if(p === null){
          // if value is null, remove param from url
          var getter = RegExp(paramobj[i] + '=\\w+');
          url = url.replace(getter, '');
        }else{
          var getter = RegExp(paramobj[i] + '=\\w+');
          url = url.replace(getter, paramobj[i] + '=' + p);
        }
      }
    }
    return (url.substr(-1) === '&')?url.slice(0, -1):url;
  },
  
  cookies: function(vname, value, expires){
    // expires = day
    if(typeof(vname) !== 'string'){
      return null;
    }
    if(value === undefined){
      //get value from cookie
      var cukyRE = new RegExp('\;{0,1}' + vname + '=(.*?);');
      try{
        return cukyRE.exec(document.cookie)[1];
      }catch(e){
        return null;
      }
    }
    var exdate = new Date();
    let names = vname.split(',');
    let values = value.split(',');
    let cs = '';
    let ending = (expires && expires>0)?';expires=' + exdate.getDate()+expires:';';
    for(let i=0,len=names.length;i<len;i++){
      cs = names[i] + '=' + escape(values[i]) + ending;
      console.log(cs);
      document.cookie = cs;
    }
    document.cookie = 'expires=' + exdate.toGMTString();
    return vname;
  },

	set_sel_opts: function(dom, opts, first, map_title, map_value){
		map_title = map_title || "title";
		map_value = map_value || "value";
		let optx = dom.options;
		if(first){
			let _o = optx[0] || document.createElement('option');
			_o.textContent = first.title;
			_o.value= first.value;
		}
		if(!opts || opts.length === 0){
			// clear
			optx.length = 0;
		}
		opts.forEach((o,j)=>{
			let _o;
			if(first){
				j++;
			}
			if(optx[j]){
				_o = optx[j];
			}else{
				_o = document.createElement('option');
				optx.add(_o);
			}
			_o.textContent = o[map_title];
			_o.value= o[map_value];
		});
		if (first){
			optx.length = opts.length + 1;
		} else {
			optx.length = opts.length;
		}
	},
	
	set_sel_opts_ex: function(dom, opts, first, map_title, map_value, exts){
		// exts: array of dataset-keynames
		map_title = map_title || "title";
		map_value = map_value || "value";
		let optx = dom.options;
		// first: the first option-item to given
		if(first){
			let _o = optx.length>0?optx[0]:document.createElement('option');
			_o.textContent = first.title;
			_o.value= first.value;
		}
		if(!opts || opts.length === 0){
			// clear
			optx.length = 0;
		}
		opts.forEach((o,j)=>{
			let _o;
			if(first){
				j++;
			}
			if(optx[j]){
				_o = optx[j];
			}else{
				_o = document.createElement('option');
				optx.add(_o);
			}
			_o.textContent = o[map_title];
			_o.value= o[map_value];
			exts.forEach((n)=>{
				_o.dataset[n] = o[n];
			});
		});
		if (first){
			optx.length = opts.length + 1;
		} else {
			optx.length = opts.length;
		}
	}
};
window._exec.__proto__ = null;


// Not all page need page_collector.use manual ini way;
function page_initor(mainpg, inifunc){
  //  TOOD: use promise for statment/data manage
  var page_collector;

  var evObj = document.createEvent('HTMLEvents');
  evObj.initEvent('load', true, true);
  var ievObj = document.createEvent('HTMLEvents');
  ievObj.initEvent('ini', false, false);

  var pgstats = {};
  pageitems = document.getElementsByClassName('divpage');
  if(pageitems.length <=0){
    return false;
  }else{
    mainpg = document.getElementById(mainpg)?mainpg:pageitems[0].id;
    pgstats[mainpg] = 0;
  }
  for(var i=0,len=pageitems.length,pid;i<len;i++){
    pid = pageitems[i].id;
    if(pid !== mainpg){
      pageitems[i].style.display = 'none';
      pgstats[pid] = 0;
    }
  }

  page_collector = {
    onload_evt: evObj,
    ini_evt: ievObj,
    main_pg: mainpg,
    cur_page: mainpg,
	pre_page: '',
    pgstats: pgstats,
    pagedatas: {},
	triggers: {},
	//NEXT ver: all click/change action are collect together
	//bind on_change-on_click to page_div
	//on_changes: [],
	//on_clicks: [],
    inner_funcs: null,

    bind_load: function(pagename, func){
      var tpg = document.getElementById(pagename);
      if(typeof(func) === 'function'){
        console.log('bing_evt: ' + func.name + ' to ' + pagename);
        tpg.addEventListener('load', func);
      }
    },

    bind_ini: function(pagename, func, at_once){
      var tpg = document.getElementById(pagename);
      if(!tpg){
        console.warn("no page named: " + pagename);
        return;
      }
      if(typeof(func) === 'function'){
        console.log('bing_inievt: ' + func.name + ' to ' + pagename);
        if(pagename === page_collector.main_pg || at_once){
          console.log('do ini act once for main page or at_once is set!');
          func();
          page_collector.pgstats[pagename]=1;
        }
        else{
          tpg.addEventListener('ini', func);
        }
      }else{
        console.warn('not able to bind a non-func to page ini!');
      }
    },

    go_page: function(pgname, fade){
		var cpage = document.getElementById(page_collector.cur_page);
		// split args
		var tpage = document.getElementById(pgname);
		if (!cpage || !tpage){
			return false;
		}
	  
		cpage.style.display = 'none';
		if(fade){
			page_collector.fade_in(tpage);
		}else{
			tpage.style.display = 'block';
		}
		page_collector.pre_page = page_collector.cur_page;
		page_collector.cur_page = pgname;
	  
		if(page_collector.pgstats[pgname] === 0){
			console.log('page ini...');
			tpage.dispatchEvent(page_collector.ini_evt);
			page_collector.pgstats[pgname] = 1;
		}
      
		// page_collector.def_onload(pgname);
		console.log('page ' + pgname + ' loading...');
		tpage.dispatchEvent(page_collector.onload_evt);
    },

    fade_in: function(tobj, display){
      tobj.style.opacity = 0;
      tobj.style.display = display || "block";

      (function fade() {
        var val = parseFloat(tobj.style.opacity);
        if (!((val += .1) > 1)) {
          tobj.style.opacity = val;
          requestAnimationFrame(fade);
        }
      })();
    },

    def_onload: function(pagename, info){
      console.log('page: ' + pagename + ' loaded!');
      if(info){
        console.log(info);
      }
    },
    
    $: function(n, v, pg){
		let pgname, n1;
		pg = pg || this.cur_page;
		// check page exists:
		if (!pg.startsWith('_') && this.pgstats[pg] === undefined){
			console.warn("no page name: " + pg);
			return;
		}
		if (typeof(pg) === 'string' && !pg.startsWith('_')){
			pgname = pg + '_';
		} else {
			pgname = page_collector.cur_page + '_';
		}
		if(n === null || n === undefined){
			if(pg === '_all'){
				return this.pagedatas;
			}
			let vs = {};
			for(k in this.pagedatas){
				if (k.startsWith(pgname)){
					vs[k] = this.pagedatas[k];
				}
			}
			return vs;
		}
		n1 = pgname + n;
		// first deal with short way of readding:
		if (v === '_$del'){
			delete this.pagedatas[n1];
			return true;
		} else if (v === undefined){
			return this.pagedatas[n1];
		} else{
			this.pagedatas[n1] = v;
			return v;
		}
	},
		
	$$: function(key, target, mode, ext){
		// to dom object: data-pckey="key"
		// mode0: key => get value
		// mode1: key, target as data to set
		// mode2: key, target, mode, ext as data
		// trigger_obj:
		// string=>querySelector(s)
		// function => apply ($v => page_collector.$(thispage)
		// store: key: {target, mode, value, preval}
		// + next ver: batch mode: key is data-object with setter/getter; {key:value}
		mode = mode || 'text';
		let $c = document.getElementById(this.cur_page);
		if(!$c){
			return false;
		}
		const $v = (n, v)=>{
			n = this.cur_page + '_' + n;
			if(!v){
				return this.pagedatas[n];
			}else{
				this.pagedatas[n] = v;
			}
		};
		const $evt_chg = (e)=>{
			// work with input item with value attribute
			let pckey=e.target.dataset.pckey;
			if(pckey && e.target.nodeName==='INPUT'){
				let $o = this.triggers[pckey];
				$o.preval = $o.value;
				$o.value = e.target.value;
			}
		};
		const $evt_ipt_clk = (e)=>{
			// click on input[radio/checkbox]
			let pckey=e.target.dataset.pckey;
			if(pckey && (e.target.type==='radio' || e.target.type === 'checkbox')){
				let $o = this.triggers[pckey];
				$o.preval = $o.value;
				$o.value = e.target.value || e.target.textContent;
			}
		};
		const $evt_update = (e)=>{
			
		};
		
		// function abc(tpl, env){function ex(tpl){console.log(this);return eval('`'+tpl+'`')};a=101,b=2,c=3;return ex.apply(env,[a,b,c])}
		// abc('startwith ${a}',k)
		function enver(tpl, env){
			tpl = tpl.replace(/\${/g, '${env.');
			return eval('`' + tpl + '`');
		}
		// => enver('hello, ${name}', {name: 'alex'}) => "hello, alex"
		// test: y='<div>list ${target}:<ul>(for fr:<li>${name}</li>)</ul></div>'
		// enver2(y,{target: 'myclass', fr:[{name:'aaa'}, {name:'bbb'},{name:'ccc'}]})
		function enver2(tpl, env){
			let exp_for = new RegExp(/\(for\s+(\w+)\:(.*?)\)/);
			let thefor = exp_for.exec(tpl);
			if(thefor){
				let forstr = '';
				env[thefor[1]].forEach((_,i)=>{forstr += thefor[2].replace(/\$\{/, '${env.' + thefor[1] + '[' + i + '].')});
				tpl = tpl.replace(thefor[0], forstr);
			}
			tpl = tpl.replace(/\$\{([^e])/g,'${env.$1');
			return eval('`' + tpl + '`');
		}
		// we got for, we got if, but no nesting
		// enver3('<div>(if show:<span>${yourname}</span>)<ul>(for names:<li>${name}</li>)</ul></div>', {show: true, yourname: 'aelx', names: [{name: 'alpha'}, {name: 'belta'}, {name: 'gamma'}]})
		function enver3(tpl, $env){
			// matchAll(plus /g) is better but chrome73+ required
			let exp_if = new RegExp(/\(if\s+(\w+)\:(.*?)\)/);
			let exp_for = new RegExp(/\(for\s+(\w+)\:(.*?)\)/);
			let theif, thefor;
			for(let i=0;i<10;i++){
				theif = exp_if.exec(tpl);
				if(theif){
					let rp="";
					if($env[theif[1]]){
						rp = theif[2];
					}
					tpl = tpl.replace(theif[0], rp);
				}else{
					break;
				}
			}
			for(let i=0;i<10;i++){
				let thefor = exp_for.exec(tpl);
				console.log(tpl);
				if(thefor){
					let forstr = '';
					$env[thefor[1]].forEach((_,i)=>{forstr += thefor[2].replace(/\$\{/g, '${$env.' + thefor[1] + '[' + i + '].')});
					tpl = tpl.replace(thefor[0], forstr);
				}else{
					break;
				}
			}
			//tpl = tpl.replace(/\$\{([^$])/g,'${env.$1');
			tpl = tpl.replace(/\$\{([^$])/g,'${$env.$1');
			return eval('`' + tpl + '`');
		}
		
		let $t = this.triggers;
		let $_ = $t[key];
		if($_){
			if(!target){
				return $_.value;
			}
			// rename target->data for clearly meaning
			let data = target, _target, dom;
			if(typeof($_.target) === 'function'){
				// function
				return $_.target(key, $v);
			}
			if (typeof($_.target) === 'string'){
				_target = [$_.target];
			} else if ($_.target instanceof Array){
				_target = $_.target;
			} else {
				return;
			}
			_target.forEach((d,i)=>{
				dom = $c.querySelector(d) || document.getElementById(d);
				if(dom){
					switch($_.mode){
						case 'value':dom.value=data;break;
						case 'text':dom.textContent=data;break;
						case 'dataset':if(key!=='pckey'){dom.dataset[key]=data};break;
						case 'check':dom.checked=data?true:false;break;
						case 'txtpl':{dom.textContent=enver($_.value, data)};break;
						case 'innertpl':dom.innerHTML=enver3($_.value, data);break;//dom.dataset.pckey=key;
						default:{
							if(dom[$_.mode]){dom[$_.mode]=data};
						}
					}
					$_.preval = $_.value;
					$_.value = data;
				}else{
					console.error("dom not found");
				}
			});
		}else{
			// add item
			console.log("on add item");
			if(typeof(target)==='string'){
				let doms = target.split(','),dom,seler,nodename;
				let okdoms =  [];
				doms.forEach((d,i)=>{
					seler = d.trim();
					dom = $c.querySelector(seler) || document.getElementById(seler);
					if(dom){
						if(dom.dataset.pckey===key){
							return;
						}
						nodename = dom.nodeName;
						okdoms.push(seler);
						if((nodename==='INPUT' || nodename === 'SELECT') && mode === 'value'){
							dom.addEventListener('change', $evt_chg);
							if(ext){dom.value=ext};
						}else if(dom.type === 'radio' || dom.type === 'checkbox'){
							dom.addEventListener('click', $evt_ipt_clk);
							if(ext){dom.checked=true};
						}else if(mode === 'txtpl' || mode === 'innertpl'){
							//pass
						}else if(typeof(ext)==='string'){
							dom.textContent = ext;
						}
						dom.dataset.pckey = key;
					}
				});
				if(okdoms.length<=0){
					console.log("no ok dom");
					return false;
				} else if (okdoms.length === 1){
					this.triggers[key] = {target: seler, mode: mode, preval: "", value: ext};
				} else {
					this.triggers[key] = {target: okdoms, mode: mode, preval: "", value: ext};
				}
			}else if(typeof(target)==='function'){
				this.triggers[key] = {target: target, mode: 'function', value: null, preval: null}
			}
			return this.triggers[key];
		}
	},
	
	_ex: function(options){
		var method = arguments[0];
		if(this.inner_funcs[method]){
			method = this.inner_funcs[method];
			Array.prototype.shift.call(arguments);
		}else if(typeof(method) === 'object' || !method){
			return this;
		}else{
			$.error('Method: ' + method + ' not exits!');
			return this;
		}
		//this === $(loader):
		let _env = {};
		let prefix = this.cur_page + '_';
		let pstart = prefix.length;
		for(k in this.pagedatas){
			if (k.startsWith(prefix)){
				_env[k.substr(pstart, 100)] = this.pagedatas[k];
			}
		}
		this._env = _env;
		return method.apply(this, arguments);
	},
  };
  window.page_collector = page_collector;
  window._PGC = page_collector;
  window.go_page = function(pagename, fade){
    if(page_collector.cur_page !== pagename){
      page_collector.go_page(pagename, fade);
    }
    //set page_collector current data everonment
  };

  $("button.backpage").on('click', function(){
    if(page_collector.pre_page){page_collector.go_page(page_collector.pre_page)};
  });
  $("button.backhome").on('click', function(){
    page_collector.go_page(page_collector.main_pg);
  });
  // var bkhs = document.querySelectorAll(".backhome");
  // for(var i=0,len=bkhs.length;i<len;i++){
  //   bkhs[i].onclick = function(){
  //     page_collector.go_page(page_collector.main_pg);
  //   }
  // }
	if(inifunc && typeof(inifunc === 'function')){
		inifunc();
	}
};

//dlg_mgm
//dialog manager
//sma:submit action
//spa: post_return data hanlder function
//sta: start inital function
var dlg_mgm = dlg_mgm || {};
dlg_mgm = (function($){
	return{
		options: {
			post_save: true
		},
		last_data: {}, // last data posted
		timeout: 3000,
		ext_values: {},
		cur_dlg : null, // object of current dialog
		dlgs : {},
		/*
		dlg pattern: {dlgname: {
			name: dlgname,
			did(string: #id of dialog), 
			fid(string: #id of form), 
			fix_data: function(postdata) or {object}
			on_submit: function: ($dlg, should return true),
			on_response: function(response)
			checkers: {}
			validate: false,
			}...}
		*/
		useful_tmpls: null,
		
		set_dlgs: function(){
			for(let d in this.dlgs){
				let dlg = this.dlgs[d];
				if(dlg.smb){
					let btn;
					if(dlg.smb.startsWith('#')){
						btn = $(dlg.smb);
					}else{
						btn = $('.' + dlg.smb);
					}
					btn.on('click', (e)=>{dlg_mgm.postform(d)});
				}
				if(dlg.clrb){
					let btn;
					if(dlg.clrb.startsWith('#')){
						btn = $(dlg.clrb);
					}else{
						btn = $('.' + dlg.clrb);
					}
					btn.on('click', (e)=>{dlg_mgm.do_clear(d)});
				}
			}
		},
		
		_$dlg: function(dlgname){
			// get the dialog from this.dlgs
			// return $dialog jquery object
			if (!dlgname){
				if (this.cur_dlg){
					return $(this.cur_dlg.did);
				}
				return undefined;
			}
			if (typeof(dlgname) === 'string'){
				if (dlgname.startsWith('#')){
					return $(dlgname);
				}else {
					return $(this.dlgs[dlgname].did);
				}
			}else if (dlgname instanceof Node){
				return $(dlgname);
			}else if (dlgname instanceof jQuery){
				return dlgname;
			}
		},
		
		_dlg: function(dlgname, keyname){
			// get the data-object of dialog in this.dlgs
			let dlg;
			if (!dlgname){
				dlg = this.cur_dlg;
			}
			if (typeof(dlgname) === 'string'){
				dlg = this.dlgs[dlgname];
			}else if (dlgname instanceof jQuery){
				dlg = this.dlgs[dlgname.prop('dlgname')];
			}else if (dlgname instanceof Node){
				dlg = this.dlgs[dlgname.id];
			}
			if (keyname === 'id'){
				return dlg.did;
			}else if (keyname){
				return dlg[keyname];
			}else{
				return dlg;
			}
		},
		
		opendlg: function(dlgname, source, title, callback){
			// OPEN a dialog with source data, show on controls
			// source: key-value data object, if source is null, open an empty dialog
			let $dlg = this._$dlg(dlgname);
			$dlg.modal({
				show: true,
			});
			if (title){
				$dlg.find('.modal-title').text(title);
			}
			if (source){
				this.set_values($dlg, source);
			}
			this.cur_dlg = this._dlg(dlgname);
			if (typeof(callback) === 'function'){
				callback();
			}
		},

		//binding input/select/radio/checkbox with attribute name to an object which stored in data_store
		//when dialog on change, react to object
		bind_vars: function(dlgname, act){
			var $tform = $dlg.find("form");
			if($tform.length === 0){
				$tform = $dlg;
			}else{
				return;
			}
			if(dlg_mgm.data_store[dlgname] === undefined || typeof(dlg_mgm.data_store[dlgname]) !== 'object'){
			  dlg_mgm.data_store[dlgname] = {};
			  dlg_mgm.data_store[dlgname].__proto__ = null;
			}else if(act === '_ini'){
			  dlg_mgm.data_store[dlgname] = dlg_mgm.get_json($tform);
			}else if(act === '_del' && dlg_mgm.data_store[dlgname]){
			  delete dlg_mgm.data_store[dlgname];
			  $tform.off('change', '[name]');
			  return;
			}
			//should bind onchange will be ok(value)
			$tform.on('change', '[name]', function(){
				var od = dlg_mgm.data_store[dlgname];
				var type = this.type || this.nodeName;
				switch(type){
					case 'radio': {
					  od[this.name] = this.value || this.nextSibling.data || this.nextSibling.innerText;
					};break;
					case 'checkbox': {
					  od[this.name] = this.checked;
					};break;
					default:{
					  od[this.name] = this.value;
					}
				}
			});
		},

		set_values: function($dlg, vars_data, clear){
			//c_or_l: clear: when a target with[name] without a vars_data[name], if set clear will clear the value
			if (typeof($dlg) === 'string' || !$dlg){
				$dlg = this._$dlg($dlg);
			}
			var $tform = $dlg.find("form");
			if($tform.length === 0){
				$tform = $dlg;
			}
			var ttype, vval;
			var c = 0;
			$tform.find('[name]').each(function(){
				var ttype = this.type || this.nodeName;
				var vname = this.getAttribute('name');
				//{varsname: value}
				vval = vars_data[vname]===undefined?null:vars_data[vname];
				if(vval === null){
					if(clear){
						this.value = '';
					}
					return;
				};
				if(['text', 'number', 'tel', 'range', 'date', 'email', 'textarea'].indexOf(ttype) >= 0){
					this.value = (vval === 'None'?'':vval);
				}else if((ttype === 'radio' || ttype === 'checkbox') && this.value === vval){
					this.checked = true;
				}else if(this.nodeName === 'SELECT'){
					for(var o,i=0,len=this.options.length;i<len;i++){
					o = this.options[i];
					if(o.value == vval || o.text == vval){
						this.selectedIndex = i;
					break;
				  }
					}
				// this.options[this.selectedIndex].text = vval;
				}else{
					this.innerText = vval;
				}
				c++;
			});
		},

		do_clear: function($dlg, bynames){
			var $tform = $dlg.find("form");
			if($tform.length === 0){
				$tform = $dlg;
			}
			if(!(bynames instanceof Array)){
				$tform.find('[name]').each(function(){
					if(this.nodeName === 'DIV'){
						this.innerHTML = '';
					}else if(this.checked){
						this.checked = false;
					}else if(this.nodeName === 'SELECT'){
						this.selectedIndex = 0;
					}else{
						this.value = ''
					}
				});
			}else{
				$tform.find('[name]').each(function(){
					if(bynames.indexOf(this.name)<0){
						return;
					}
					if(this.nodeName === 'DIV'){
						this.innerHTML = '';
					}else if(this.checked){
						this.checked = false;
					}else if(this.nodeName === 'SELECT'){
						this.selectedIndex = 0;
					}else{
						this.value = ''
					}
				});
			}
		},

		ez_validate: function(form_or_datas, checkrs, alert){
			const vali_regs = {
				number: /^-?\d+$/,
				date: /^\d{4}(\-)\d{1,2}\1\d{1,2}$/,
				phone: /^1[3|4|5|8][0-9]\d{4,8}$/,
				email:  /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/,
				chinese: /^[\u0391-\uFFE5]+$/,
				english: /^[A-Za-z]+$/,
				idnum: /^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
			}
			const ichkr = function(value, cks){
				let ckrts = true,rt,ck;
				for(var i=0,len=cks.length;i<len;i++){
					ck = cks[i];
					if (ck === 'require'){
						rt = value?true:false;
					}else if (ck.indexOf(':')>0){
						var tokens = ck.split(':');
						switch(tokens[0]){
							//st: small than, lt: larger than; "require,LE:0,SE:100" .etc
							case 'ST': rt = value<parseInt(tokens[1])?true:false;break;
							case 'LT': rt = value>parseInt(tokens[1])?true:false;break;
							case 'SE': rt = value<=parseInt(tokens[1])?true:false;break;
							case 'LE': rt = value>=parseInt(tokens[1])?true:false;break;
							case 'BT': rt = (value>parseInt(tokens[1]) && value<parseInt(tokens[2]))?true:false;break;
							default: rt=false;
						}
					}else{
						try{if(vali_regs[ck].test(value)){rt = true;}}catch(e){rt = false}
					}
					ckrts = ckrts && rt;
				}
				return ckrts;
			}

			var rts = true;
			var rt;
			if(typeof(form_or_datas) === 'object'){
				//{key1:val1,key2:val2...}, {key1:chk1, key2:chk2...}
				for(var k in checkrs){
					// once a false , direct return; if all check: rt = ichkr(form_or_datas[k], checkrs[k].split(','));rts=rts&&rt;
					rts = rts && ichkr(form_or_datas[k], checkrs[k].split(','));
				}
				return rts;
			}
			$(form_or_datas).find('[name]').each(function(){
				var tn = this.name;
				var ckr=checkrs?(checkrs[tn] || this.dataset.validate):this.dataset.validate;
				if(tn && ckr){
					var vv = this.value || this.innerText;
					if (typeof(ckr) === 'function'){
						rt = ckr(vv);//ckr is function: return true/false
						rt = (rt === true || rt === false)?rt:false;
					}else{
						rt = ichkr(vv, ckr.split(','))
					}
					if(alert && !rt){
						$(this).closest('div').prop('classList').add('has-error');
					}else{
						$(this).closest('div').prop('classList').remove('has-error');
					}
					rts = rts && rt;
				}
			});
			return rts;
		},

		//json removed
		get_json: function($dlg, item_names, item_mode, sp_ids, fillvals, skip_space){
			const gv = function(ipt){
				switch(ipt.type){
					case "text":
					case "date":
					case "number":return ipt.value;
					case "select-multiple": {let rt=[];sos=ipt.selectedOptions;for(let i=0,len=sos.length;i<len;i++){rt.push(sos[i].value)};return rt.join(',');}
					//case "select-one":ipt.options[ipt.selectedIndex].value;
					case "radio": if(ipt.checked){return ipt.value}else{return ''};
					case "checkbox": if(ipt.checked){return ipt.value}else{return ''};
					default: return ipt.value || '';
				}
			}
			var $tform = $dlg.find("form");
			if($tform.length === 0){
			  $tform = $dlg;
			}
			var rta = {};
			var imode = 0;//0:default;1:item_name to collect;2:item_name to remove
			if($.isArray(item_names) && item_mode !== '-'){
				for(var i=0,len=item_names;i<len;i++){
					rta[item_names[i]] = null;
				}
				imode = 1;
			}else{
				$tform.find('[name]').each(function(){
					var name = this.getAttribute('name');
					if(imode === 1 && rta[name] !== null){
					  // if imode===1, rta[name] should have been set to null,
					  // so when rta[name] !== null, it's no need to collect
					  return;
					}
					if(this.nodeName === 'DIV'){
						var thisvar = [];
						$(this).find(':input').each(function(){
							var v = gv(this);
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
					var v = gv(this);
					if (rta[name]){
						//pass when already have value with the same name(avoiding Conflict)
					}else if(v){
						rta[name] = v || fillvals || fillvals[name];
					}
				});
				// if there is some item don't wannt to post
				if($.isArray(item_names) && item_mode === '-'){
					for(var i=0,len=item_names.length;i<len;i++){
						delete rta[item_names[i]];
					}
				}
			}
			//special target withou a [name] attribute
			if(sp_ids){
				var tv;
				[].concat(sp_ids).map(function(v, i){
					tv = $tform.find('#' + v).text();
					if(tv){rta[v] = tv}
				});
			}
			return rta;
		},

		post_form: function($dlg, url, pdata, fix_data, datatype){
			var dlg = this._dlg($dlg);
			url = url || dlg.url || $dlg.find("form").attr('action');
			//specal data to post
			pdata = pdata || this.get_json($dlg);
			fix_data = fix_data || dlg.fix_data;
			if (typeof(fix_data) === 'function'){
				fix_data(pdata);
				console.log(pdata);
			} else if ($.isPlainObject(fix_data)){
				Object.assign(pdata, fix_data);
			}
			if(this.options.post_save){
				this.last_data[dlg.name] = pdata;
			}
			$.ajax({
				timeout: this.timeout,
				type: 'post',
				url: url,
				data: pdata,
				dataType: datatype || 'json'
			}).success(function(result){
				let on_response = dlg.on_response;
				if(typeof(on_response) === 'function'){
					on_response.call(dlg, result);
					//on_response(result);
				}else if ($.isPlainObject(result)){
					alert("done_post: \n" + result.msg);
				}else if(typeof(result)==='string'){
					alert('done_post: \n' + result);
				}else{
					alert('post done!');
				}
			}).fail(function(jqXHR, textStatus, errorThrow){
				console.warn(textStatus);
			});
		},

		go_submit: function(dlgname){
			// rtype: 'text', 'json', 'xml', ....
			let dlg = this._dlg(dlgname);
			let $dlg = this._$dlg(dlgname);
			var rtype = rtype || 'json';
			if (dlg.validate){
				if (!this.ez_validate($dlg, dlg.checkers, true)){
					alert("错误的输入！");
					return;
				}
			}
			if (dlg.on_submit && typeof(dlg.on_submit) === 'function'){
				if(!dlg.on_submit($dlg)){
					return;
				}
			}
			this.post_form($dlg);
			if($dlg.hasClass('modal')){
				$dlg.modal('toggle');
			}
		},

		add_item: function(tmpl, values, dep_dom, pos, ext_attrs){
			//dep_dom: item depend on dep_dom with pos(sition) of before/after/append
			var tmpl_split = ((tmpl.length >= 10)?tmpl:(dlg_mgm.useful_tmpls[tmpl] || '')).split(/\#\{(\w+)\}/g);
			if(tmpl_split.length <= 0){
				return false;
			}
			var rts, tobj;
			var dep_dom = typeof(dep_dom) === 'string'?$(dep_dom):(dep_dom.length === 1?dep_dom:null);
			var pos = pos || 'append';
			if(!(dep_dom && ['after', 'before', 'append'].indexOf(pos)>=0)){
				console.warn('add_item with out correct dep_dom and/or pos!');
				return false;
			}
			// if batch, will ignore the ext_attrs
			if (values instanceof Array){
				for(var i=0,len=values.length;i<len;i++){
					rts = '';
					tmpl_split.map(function(v,i){
						if(v && i%2===1){rts += (values[v] || '')}else{rts += v}
					});
					dep_dom[pos](rts);
			  }
			}else{
				rts = ''
				tmpl_split.map(function(v,i){
				if(v && i%2===1){rts += (values[v] || '')}else{rts += v}});
				tobj = $(rts);
				if(ext_attrs){
					for(var attr in ext_attrs){
						tobj.attr(attr, ext_attrs[attr]);
					}
				}
				dep_dom[pos](tobj);
			}
		},
		
		inital: function(dlgs){
			// bind actions to button (default)
			if (dlgs){
				this.dlgs = dlgs;
			}
			Object.values(this.dlgs).forEach((d)=>{
				let dlg = document.querySelector(d.did);
				$(dlg).prop('dlgname', d.name);
				if(d.smb){
					let btn = dlg.querySelector(d.smb);
					if(btn){
						btn.onclick = ()=>{
							let _d = dlg_mgm._dlg();
							let _a = _d['on_submit'];
							if(_a){
								_a.call(dlg_mgm, _d);
							} else {
								dlg_mgm.go_submit();
							}
						};
						console.log("bind submit to " + d.did);
					}
				}
				if (d.on_changes){
					dlg.onchange = (e)=>{
						let _t = e.target.name;
						let _v = e.target.value;
						let _d = dlg_mgm._dlg();
						let _a = _d.on_changes[_t];
						if(_a){
							_a.call(dlg_mgm, _t, _v);
						}
					};
				}
			});
		},
	  
		ini_vals: function(keys){
			try{
				dlg_mgm.ext_values.__proto__=null
			}catch(e){
				console.warn("not able to set __proto__ to null!");
			}
			if (typeof(keys) === "string"){
				keys = keys.split(',').map((x)=>{return x.trim()});
			}
			if (keys instanceof Array){
				for (let x=0,len=keys.length;x<len;x++){
					dlg_mgm.ext_values[keys[x]] = undefined;
				}
			}else if (typeof(keys)==="object"){
				allkeys = Object.entries(keys);
				for (let x=0,len=allkeys.length;x<len;x++){
					dlg_mgm.ext_values[allkeys[x][0]] = allkeys[x][1];
				}
			}
			Object.seal(dlg_mgm.ext_values);
	  },
	  
		$: function(n, v){
			// n must in ext_values and ext_values must be ini_vals at begining
			if(n in dlg_mgm.ext_values){
				if (v === undefined){
					return dlg_mgm.ext_values[n];
				} else{
					dlg_mgm.ext_values[n] = v;
					return v;
				}
			}else if ($.isPlainObject(n)){
				for(let k in n){
					dlg_mgm.ext_values[k] = n[k];
				}
			} else {
				return Object.entries(dlg_mgm.ext_values);
			}
		},
	  // $ : function(n,v){if(v===undefined){return dlg_mgm.ext_values[n]}else{dlg_mgm.ext_values[n]=v}},
	}
//dialog init
})(jQuery);



//stable
// no core_tmpl_str, each row_template should work with: ${row.variablename}
// try to update with loan keepper
(function ($) {

  var page_bar = {
    curdiv: '',
    //filter_zoom: div's id, collect data
    filter_zoom: '',
    pagedatas: {},
    tmpls: {
      innerdiv: '<div class="input-group" tblpages="${pages}"><span class="input-group-btn">all:??</span></div>',
      innerbtns: '<span class="input-group-btn"><button class="btn btn-default tblbar_gofirst" type="button"><i class="icon icon-fast-backward"></i></button><button class="btn btn-default tblbar_gopre" type="button"><i class="icon icon-chevron-left"></i></button></span><input type="text" class="form-control tblbar_setpage" placeholder=""><span class="input-group-btn"><button class="btn btn-default tblbar_gopage" type="button"><i class="icon icon-check"></i></button><button class="btn btn-default tblbar_gonext" type="button"><i class="icon icon-chevron-right"></i></button><button class="btn btn-default tblbar_golast" type="button"><i class="icon icon-fast-forward"></i></button><button class="btn btn-default tblbar_refresh" type="button"><i class="icon icon-spin icon-refresh"></i></button><button class="btn btn-default tblbar_start" type="button"><i class="icon icon-bolt"></i></button></span><div class="input-group-btn"><button type="button" class="btn btn-default pagesize" tabindex="-1">20</button><button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" tabindex="-1"><span class="caret"></span><span class="sr-only">更多数量</span></button><ul class="dropdown-menu pull-right" role="menu"><li><a href="#">20</a></li><li><a href="#">50</a></li><li><a href="#">100</a></li></ul></div>'
    },
    assign: function(div){
      if($(div).length === 1){
        page_bar.curdiv = div;
        return page_bar;
      }else{
        return null;
      }
    },

    //create bar and bind actions
    create: function(div, pages){
      let $div = $(div || page_bar.curdiv);
      pages = pages || 0;
      let idiv = $(`<div class="input-group" tblpages="${pages}"><span class="input-group-btn">all:??</span></div>`);
      idiv.append(page_bar.tmpls.innerbtns);
      if(pages>0){
        idiv.find('input').attr('placeholder', '1 / ' + pages);
      }
      $div.empty().append(idiv);
      // if(pages>0){
        // page_bar.set_page(div, 1, pages);
      // }
      return page_bar;
    },

    checkme: function(div){
      let $div = $(div || page_bar.curdiv);
      if($div.prop('id')){
        return true;
      }else{
        return false;
      }
    },

    //destroy
    destroy: function(div){},

    set_page: function(div, pagenum, pages){
      var tobj = $(div || page_bar.curdiv);
      var pagebox = tobj.find('input');
      if(pagenum <= 1 && pages>0){
        tobj.find('> div').attr('tblpages', pagenum);
        pagebox.prop('placeholder', '1 / ' + pages);
        return pages;
      }
      if(pages && pages > pagenum){
        tobj.find('> div').attr('tblpages', pages);
      }else{
        var pages = parseInt(tobj.find('> div').attr('tblpages'));
      }
      if(tobj.length !== 1){
        return false;
      }
      if(!pages || pages < pagenum){
        return false;
      }
      // tobj.find('input').val(pagenum + ' / ' + pages);
      pagebox.prop('placeholder', pagenum + '/' + pages);
    },
  };

  var tbl_funcs = {
    clear: function(tbl_obj, keepheader){
			let tobj;
			if(typeof(tbl_obj) === 'string'){
				tobj = document.getElementById(tbl_obj);
			}
			let rows = tobj.tBodies[0].rows;
			keepheader = keepheader || true;
			if(rows.length > 0){
				//tobj.empty();
				let i = 0;
				if(keepheader){
					i = 1;
				}
				for(len=tobj.prop('rows').length;i<len;i++){
					rows[i].innerHTML === "";
				}
			}
    },

    addrows: function(tbl_obj, tmpl, rowsdata, prtmnt){
      if (!(rowsdata instanceof Array) || rowsdata.length <= 0){
		console.warn('no data to list in table!');
        return;
      }
      //tmpl: #{}
      const tbody = $(tbl_obj).find('tbody')[0];
		//we don't have to clear first
      let idx=0;
      if(typeof(prtmnt)==='function'){
        let row,rowstr;
        rowsdata.forEach((r)=>{
          row = prtmnt(r);
		  if (!row){
			  return;
		  }
          row['rownum'] = ++idx;
          if(!row['rowid']){row['rowid']=idx}
          rowstr = eval('`' + tmpl + '`');
		  tbody.append(rowstr);
        });
        return idx;
      }
	  // if no prompt
      rowsdata.forEach((row)=>{
        row['rownum'] = ++idx;
        if(!row['rowid']){row['rowid']=idx}
        rowstr = eval('`' + tmpl + '`');
		tbody.append(rowstr);
      });
      return idx;
    },
		
	setrows: function(tbl_obj, tmpl, rowsdata, prtmnt, checker){
		// upgrade without clear
		if (!rowsdata || rowsdata.length <= 0){
			console.warn('no data to list in table!');
			return;
		}
		let tbody = $(tbl_obj).find('tbody');
		//we don't have to clear first
		let idx=0;
		let prerows = tbody.prop('rows')?tbody.prop('rows').length:0;
		if(typeof(prtmnt)==='function'){
			let row,rowstr;
			rowsdata.forEach((r)=>{
				row = prtmnt(r);
				if(!row){
					return;
				}
				row['rownum'] = idx + 1;
				if(!row['rowid']){row['rowid'] = idx + 1}
				rowstr = eval('`' + tmpl + '`');
				if(prerows > 0 && idx<prerows){
					tbody.prop('rows')[idx].outerHTML = rowstr;
				}else{
					tbody.append(rowstr);
				}
				idx++;
			});
		}else{
			rowsdata.forEach((row)=>{
				row['rownum'] = idx + 1;
				if(!row['rowid']){row['rowid'] = idx + 1}
				rowstr = eval('`' + tmpl + '`');
				if(prerows > 0 && idx<prerows){
					tbody.prop('rows')[idx].outerHTML = rowstr;
				}else{
					tbody.append(rowstr);
				}
				idx++;
			});
		}
		if(prerows>idx){
			rows = tbody[0].rows;
			for(let i=idx;i<prerows;i++){
				rows[idx].innerHTML="";
			}
		}
		return idx;
	},
	
	add_row: function($tbl_obj, pos, row, tmpl){
		var tbody = $tbl_obj.find('tbody')[0];
		// table rows = head + body rows
		let row_num = tbody.rows.length; // tBodies[0].rows = tbl.rows - 1
		if(row_num === 0){
			pos = 0;
		}else if(pos === -1 || pos > row_num){
			pos = row_num;
		}
		let tr = tbody.insertRow(pos);
		tr.outerHTML = eval('`' + tmpl + '`');
		return pos;
	},

    del_rows: function(tbl_obj, row_th, count){
		// row_th starts from 0
		if(row_th >= 0){
			let tbody = $(tbl_obj).find('tbody')[0];
			let rows = tbody.rows;
			let count = count || 1, rt = [];
			while(count > 0){
				rt.push(rows[row_th].getAttribute('rownum'));
				tbody.deleteRow(row_th);
				count--;
			}
			return rt;
		}
    },
	
	ui_arange: function($tbl_obj, col_idx, isdesc, converter, row_from, row_end){
		// 按照指定列[从0开始], 重新排列table行，仅对UI进行操作;
		// converter: 函数，给出则通过converter对col进行处理返回的数据为比较值[返回int]
		// isdesc：是否降序； row_from/row_end[未完成]
		const def_converter = (v) => {
			//v allways td.textContent
			let v2 = parseFloat(v);
			if(isNaN(v2)){
				return null;
			}
			return v2;
		}
		row_from = row_from || 0;
		converter = converter || parseFloat;
		let tbd = $tbl_obj.find('tbody')[0];
		if (!tbd){
			console.error("no table!");
			return;
		}
		let trows = tbd.rows;
		row_end = (row_end || 1000)>trows.length?trows.length:row_end;
		let source = [], ranger = [], node0;
		if (converter){
			for(let i=0,len=row_end-row_from;i<len;i++){
				source.push(converter(trows[i].childNodes[col_idx].textContent));
			}
		} else{
			for(let i=0,len=row_end-row_from;i<len;i++){
				source.push(trows[i].childNodes[col_idx].textContent);
			}
		}
		//console.log(source);
		if (isdesc){
			// 降序[返回convertor 返回null的，自动最下]
			for(let x,v,i=0,len=source.length;i<len;i++){
				v = source[i];
				if(v === null){
					ranger.push(null)
					continue
				}
				x = 0;
				for(let j=0,len2=source.length;j<len2;j++){
					if(v<source[j]){
						x++;
					}
				}
				ranger.push(x);
			}
		} else {
			for(let x,v,i=0,len=source.length;i<len;i++){
				v = source[i];
				if(v === null){
					ranger.push(null)
					continue
				}
				x = 0;
				for(let j=0,len2=source.length;j<len2;j++){
					if(v>source[j]){
						x++;
					}
				}
				ranger.push(x);
			}
		}
		//console.log(ranger);
		// take ranger [3,7,2,5,4,1,2....] like
		let arch_node,target;
		// rowIndex: starts with 1 becourse a header row exists; but trows allways starts with 0...
		let _trows = [...trows];
		for(let cc=0,i=0,len=ranger.length;i<len;i++){
			if(ranger[i] === null){
				break;
			}
			arch_node = trows[cc++];
			for(let j=0;j<len;j++){
				if (ranger[j] === i){
					target = _trows[j];
					if (target === arch_node){}else{
						console.log("switch on " + target.rowIndex + " before " + arch_node.rowIndex);
						tbd.insertBefore(target, arch_node);
					}
					break;
				}
			}
		}
	},
	
  };

  var methods = {
    init: function(options){
      this.each(function(){
        var tbl_obj = $(this);
        var settings = tbl_obj.data('stable');
        if(!settings){
          var defaults = {
			filter_zoom: '',
			filter_params: null,
            row_tmpl: '',
            source_url: '', //from url get json data
			last_request: '',
			key_name: '',
			last_id: 0,
            tbl_bar: '',
            tbl_pages: 0, // count page
            tbl_cur_page: 0, // current page
            tbl_offset: 0,  // 1->last item index
            page_limit: 20,
            autoload: true, //after initial load data immediatly
            prtmnt: null, // row-data-formating:(row_data)=>{return new-row_data}
            pagedata: null, //VER+: set to object for arrange/re_sort
            after_gopage: null,
			selections: null,
			// sort
			sort_enable: false,
			sort_converters: null, // functions that use for covernting
            // head checkbox
            allsel_chkbx: null,
            assist_checker: null,
            // [[name, class, action], ...]
			extra_click: null,
            innerbtn_actions: []
          };
          settings = $.extend({}, defaults, options);
        }else{
          settings = $.extend({}, settings, options);
        }
        if(!settings.row_tmpl){
          var tmpl = '<tr rowid="#{row.rowid}">';
          for(var i=0,len=tbl_obj[0].rows[0].cells.length;i<len;i++){
            tmpl += '<td>#{row.cell_content}</td>';
          }
          tmpl += '</tr>'
          settings.row_tmpl = tmpl;
        }
		// action on table:
		// click on a row for single-selection
		tbl_obj.find("tbody").on('click', 'tr', {tbl: tbl_obj.attr('id'), act: settings.extra_click}, function(event){
			let tdata = $('#' + event.data.tbl).data('stable');
			if(tdata['curtr']){
				tdata['curtr'].classList.remove('active');
			}
			tdata['curtr'] = this;
			let idx = this.getAttribute('rownum');
			tdata['selections'] = tdata.pagedata[idx];
			this.classList.add('active');
			if(event.data.act){
				event.data.act(tdata['selections']);
			}
		});
        //bind actions to buttons
        for(var i=0,len=settings.innerbtn_actions.length;i<len;i++){
          var actset = settings.innerbtn_actions[i];
          if(actset[1].substr(0,1) === '#'){
            $(actset[1]).on('click', actset[2]);
          }else{
            tbl_obj.on('click', '.' + actset[1], {action: actset[2]},function(event){
              var trow = $(this).closest('tr')[0];
              // return the DOM tr not the jquery tr
              event.data.action(trow);
            });
          }
        }
		// filterzoom action on radio
		if(settings.filter_zoom && typeof(settings.filter_zoom)==='string'){
			$(settings.filter_zoom).on('click', 'input:radio', function(event){
				methods['go_page'](1, true, null, false, tbl_obj);
			});
		}
		// checkbox for all select
		if(settings.allsel_chkbx){
			$(settings.allsel_chkbx).on("click", function(){
				//test first row for checkbox
				let $table = $(this).closest("table");
				let checker = $table.data('stable').assist_checker;
				console.log(checker);
				if(this.checked){
					console.log('select all');
					$table.stable('toggle_checks', true, checker);
					//methods['toggle_checks'](true, settings.assist_checker);
				}else{
					console.log('unselect all');
					$table.stable('toggle_checks', false, checker);
					//methods['toggle_checks'](false, settings.assist_checker);
				}
			});
		}
        tbl_obj.data('stable', settings);
        //pagebar
        if(settings.autoload){
          methods['go_page'](1, true, null, false, tbl_obj);
        } else {
			tbl_obj.data('stable').pagedata = {};
		}
        if(settings.tbl_bar){
			// page_bar.assign(settings.tbl_bar).create('', settings.tbl_pages);
			$(settings.tbl_bar).on('click', 'button', {tbl: tbl_obj.attr('id')}, function(event){
				// tblbar_gofirst/pre/gopage/next/last
				var $stable = $('#' + event.data.tbl);
				var btc = this.getAttribute('class').split(/\s+/).pop();
				var cpage = $stable.data('stable')['tbl_cur_page'];
				var allpage = $stable.data('stable')['tbl_pages'];
				if(!allpage){
				  return false;
				}
				var topage = 0;
				switch(btc){
					case 'tblbar_gofirst': topage = cpage===1?0:1;
					break;
					case 'tblbar_gopre': topage = cpage>1?cpage-1:0;
					break;
					case 'tblbar_gonext': topage = cpage===allpage?0:cpage+1;
					break;
					case 'tblbar_golast': topage = cpage===allpage?0:allpage;
					break;
					case 'tblbar_gopage': {
						topage = parseInt($(this).closest('div').find('input').val()) || 0;
						topage = (topage>allpage || topage<1 || topage === cpage)?0:topage;
					};
					break;
					case 'tblbar_refresh': topage = cpage;
					break;
					case 'tblbar_start': {};
					break;
				}
				if(topage===0){
					$(this).closest('div').find('input').prop('placeholder', cpage + '/' + allpage).val('');
					return;
				}else{
					$(this).closest('div').find('input').prop('placeholder', topage + '/' + allpage).val('');
					$stable.stable('go_page', topage);
				}
			});
			// li of pagesize
			$(settings.tbl_bar).on('click', 'li', {tbl: tbl_obj}, function(event){
				let cont = this.innerText;
				this.parentElement.previousElementSibling.previousElementSibling.innerText = cont;
				tbl_obj.data('stable').page_limit = parseInt(cont);
			});
        }
      });
    },
		
	clear: function(force){
		//update mode:
		if(force){
			tbl_funcs.clear(this);
			return;
		}
		let trows = this.length?this[0].tBodies[0].rows:this.tBodies[0].rows;
		for(let i=0;i<trows.length;i++){
			if(trows[i].innerHTML !== ""){
				trows[i].innerHTML = '';
			}
		}
	},
    
    set_page_data: function(pagedata, sort_func){
		// pagedata pass in is array and convert to data-object to store
		//for debugging
		let tbl_obj = $(this);
		let cursetting = tbl_obj.data('stable');
		let _pagedata = {};
		let kn = cursetting.key_name;
		pagedata.forEach((n)=>{
			_pagedata[n[key_name]] = n;
		});
		//console.log(cursetting);
		tmpl = cursetting['row_tmpl'];
		//tbl_funcs.clear(tbl_obj);
		if (typeof(sort_func) === 'function'){
			pagedata = pagedata.sort(sort_func);
		} else if (typeof(sort_func) === 'string'){
			// inner sort key-name
			//;pass
		}
		tbl_funcs.setrows(tbl_obj, tmpl, pagedata, cursetting['prtmnt']);
		if(cursetting['tbl_bar']){
			page_bar.assign(cursetting['tbl_bar']).create(null, 1);
		}
		cursetting['tbl_pages'] = 1;
		cursetting['pagedata'] = _pagedata;
	},
		
	set_row: function(row_line, rowdata){
		//row_line: starts with 1
		let setting = tbl_obj.data('stable');
		let tbl_obj = $(this),
			tmpl = setting.row_tmpl,
			prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		if (!row){
			return false;
		}
		tbl_obj.find('tbody')[0].rows[row_line-1].outerHTML =  eval('`' + tmpl + '`');
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
		return row;
	},
	
	set_row_byid: function(keyid, rowdata){
		let tbl_obj = $(this);
		let setting = tbl_obj.data('stable');
		let pdata = setting.pagedata,
			keyname = setting.key_name,
			tmpl = setting.row_tmpl,
			prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		if (!row){
			return false;
		}
		let trows = tbl_obj.find('tbody')[0].rows
		for(let row_idx=0, rlen = trows.length;row_idx<rlen;row_idx++){
			if (trows[row_idx].getAttribute('rownum') == keyid){
				trows[row_idx].outerHTML =  eval('`' + tmpl + '`');
				console.log('set_row_byid: row text is set!');
				pdata[keyid] = rowdata;
				return;
			}
		}
		alert("set_row_byid: not found!");
	},
	
	del_row_byid: function(keyid){
		let tbl_obj = $(this);
		let setting = tbl_obj.data('stable');
		let pdata = setting.pagedata,
			keyname = setting.key_name;
		let trows = tbl_obj.find('tbody')[0].rows
		for(let row_idx=0, rlen = trows.length;row_idx<rlen;row_idx++){
			if (trows[row_idx].getAttribute('rownum') == keyid){
				trows[row_idx].outerHTML = "";
				console.log('del_row_byid: row text is done!');
				delete pdata[keyid];
				return;
			}
		}
		alert("del_row_byid: not found!");
	},

	del_row: function(start, len){
		// starts with 1
		if(start<1){
			return false;
		}
		start = start - 1;
		var max = this.tBodies[0].rows.length;
		len =  max - len - start > 0?len:max - start;
		let dels = tbl_funcs.del_rows(this, start, len, this.data('stable').key_name);
		if(dels.length > 0){
			let pd = this.data('stable').pagedata;
			dels.forEach((n)=>{
				delete pd[n];
			});
		}
    },
	
	get_row: function(arg, get_source, findby, not_scroll){
		// get a row
		// if get_source: get the source data from pagedata
		$tbl = this[0];
		let r,rm,rd;
		if (typeof(arg) === "number"){
			// row index
			r = $tbl.tBodies[0].rows[arg+1];
			rm = r.getAttribute('rownum');
		} else if (typeof(arg) === "string"){
			let rows = $tbl.tBodies[0].rows;
			let like_first=-1, match_first=-1;
			for (let i=0,len=rows.length;i<len;i++){
				r = rows[i];
				let cells = r.cells;
				for (let j=0,lenj=cells.length;j<lenj;j++){
					if (cells[j].textContent === arg && match_first === -1){
						match_first = i;
						break;
					}else if (like_first === -1 && cells[j].textContent.indexOf(arg) >= 0){
						like_first = i;
					}
				}
				if (match_first > -1){
					r = rows[match_first];
					break;
				}
			}
			if (match_first === -1 && like_first > -1){
				r = rows[like_first];
			}
		}
		if (!r){
			return;
		}
		if (!not_scroll){
			window.scrollTo(0, r.offsetTop);
		}
		r.click();
		if (get_source && findby){
			let pdata = $($tbl).data("stable")["pagedata"];
			for(let i=0,len=pdata.length;i<len;i++){
				if (pdata[i][findby] == rm){
					return pdata[i];
				}
			}
			return null;
		}
		return r;
	},
	
	append_row: function(rowdata){
		let setting = this.data('stable');
		let prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		tbl_funcs.add_row(this, -1, row, setting.row_tmpl);
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
    },
	
	insert_row: function(pos, rowdata){
		if(pos === 0){
			alert("row pos starts with 1");
			return false;
		}
		let setting = this.data('stable');
		let prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		tbl_funcs.add_row(this, pos-1, row, setting.row_tmpl);
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
	},
    
    toggle_checks: function(check, checker){
      let tbody = this.length?this.find('tbody')[0]:this.tBodies[0];
      let rows = tbody.rows;
      if(rows[0].cells[0].firstElementChild.type !== 'checkbox'){
        return false;
      }
      if(check){
        checked = true;
      }else if(check === undefined){
        // when not set, auto reverse
        checked = 0;
      }else{
        checked = false;
      }
      for(let i=0,len=rows.length;i<len;i++){
        if(checker && !checker(rows[i])){
          continue;
        }
        if(checked === 0){
          checked = rows[i].cells[0].firstElementChild.checked?false:true;
        }
        rows[i].cells[0].firstElementChild.checked = checked;
      }
    },

    go_page: function(pagenum, summary, params, no_tbl_bar, iniobj){
		var tbl_obj = iniobj?$(iniobj):$(this);
		var pagenum = pagenum || 1;
		if (typeof(pagenum) === 'number'){
			var cursetting = tbl_obj.data('stable');
			var allparam = {page: pagenum, page_limit: cursetting['page_limit']};
			// collect filters
			let fz = cursetting['filter_zoom'];
			if (fz){
				if(typeof(fz) === 'string'){
					let cfs = dlg_mgm.get_json(fz, null, null, null, null, true);
					$.extend(allparam, cfs);
				}else if(typeof(fz) === 'object'){
					$.extend(allparam, fz);
				}
			}
			if(summary || pagenum === 1 || !cursetting['tbl_pages']){
				allparam['summary'] = 'yes';
				summary = true;
			}else if (cursetting['last_id'] > 0){
				allparam['last_id'] = cursetting['last_id'];
			}
			// if(cursetting['extkeys']){
			//   $.extend(allparam, cursetting['extkeys']);
			// }
			params = params || cursetting['filter_params'];
			if(params){
				//$.extend(allparam, params);
				Object.assign(allparam, params);
			}
			var url = _exec.make_urlparam(allparam, cursetting['source_url']);
			cursetting['last_request'] = url;
		}else if(pagenum === 'reflash'){
			var url = cursetting['last_request'];
			if(!url){
				return false;
			}
		}
		dout('gopage now', url);
		$.getJSON(url, function(rt, stat){
			if(!rt.data){
				console.warn("no data to list in table!");
				return false;
			}else if(rt.success && rt.success === 'no'){
				console.error("failure get data!\n" + rt.msg);
				return false;
			}
			///////////////////////// For Tencent smart school: using dataList&pageInfo
			let data = rt.data.dataList?rt.data.dataList:rt.data;
			let pinfo = rt.data.pageInfo?rt.data.pageInfo:{total: Math.ceil(rt.dlen/cursetting['page_limit'])};
			if(summary){
				if(pinfo.total){
					cursetting['tbl_pages'] = parseInt(pinfo.total);
				}else{
					cursetting['tbl_pages'] = 1
				}
				if (cursetting['tbl_bar'] && !no_tbl_bar){
					console.log('create toolbar');
					page_bar.create(cursetting['tbl_bar'], cursetting.tbl_pages);
					page_bar.set_page(cursetting['tbl_bar'], pagenum, cursetting.tbl_pages);
				}
			}
			let kn = cursetting['key_name'];
			let _data = {};
			data.forEach((n)=>{
				_data[n[kn]] = n;
			});
			cursetting['pagedata'] = _data;
			tbl_funcs.setrows(tbl_obj, cursetting['row_tmpl'], data, cursetting['prtmnt']);
			cursetting['tbl_offset'] = cursetting['tbl_cur_page'] * cursetting['page_limit'] + data.length;
			if (cursetting['key_name']){
				let last_row = data[data.length - 1];
				cursetting['last_id'] = last_row[kn];
			}
			//tbl_funcs.clear(tbl_obj);
			//tbl_funcs.addrows(tbl_obj, cursetting['row_tmpl'], data, cursetting['prtmnt']);
			if(cursetting['after_gopage']){
				cursetting['after_gopage'](data);
			}
      });
      cursetting['tbl_cur_page'] = pagenum;
    },
  };

  $.fn.stable = function (options){
    var method = arguments[0];
    if(methods[method]){
      method = methods[method];
      Array.prototype.shift.call(arguments);
    }else if(typeof(method) === 'object' || !method){
      method = methods.init;
    }else{
      $.error('Method: ' + method + ' not exits!');
      return this;
    }
    //this === $(loader):
    return method.apply(this, arguments);
  };  
})(jQuery);