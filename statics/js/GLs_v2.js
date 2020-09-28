//GLS v2
// ES6
// ZUI.1.81
// Work for loankeeper with some special defination
__glsv2version__ = 3
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
    if(vname && value === undefined){
      //get value from cookie
      var cukyRE = new RegExp('\;{0,1}' + vname + '=(.*?)($|;)');
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
  
  tplstr: function(tplr, datas, filter_func){
		let tpl,rts="",localdata;
    if (typeof(tplr)==="string"){
      tpl = document.getElementById(tplr);
      if (!tpl){
        return false;
      }
    }else if(tplr instanceof jQuery){
      tpl = tplr[0];
    }
    //tpl ${data.varname}
    if(filter_func && typeof(filter_func) === 'function'){
      localdata = filter_func(datas);
    }else{
      localdata = datas;
    }
    with(localdata){
      rts = eval( '`' + tpl.innerHTML + '`');
    }
    return rts;
  },

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
					// func.call(tpg);
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
			var tpage,cpage = document.getElementById(page_collector.cur_page);
			if (pgname === -1){
			 //backpage
				tpage = page_collector.pre_page;
			}else{
				tpage = document.getElementById(pgname);
			}
			if (!cpage || !tpage){
				return false;
			}
			if(page_collector.pgstats[pgname] === 0){
				console.log('page ini...');
				tpage.dispatchEvent(page_collector.ini_evt);
				page_collector.pgstats[pgname] =1;
			}
			cpage.style.display = 'none';
			if(fade){
				page_collector.fade_in(tpage);
			}else{
				tpage.style.display = 'block';
			}
			page_collector.pre_page = page_collector.cur_page;
			page_collector.cur_page = pgname;
			// page_collector.def_onload(pgname);
			console.log('page ' + pgname + ' loading...');
			tpage.dispatchEvent(page_collector.onload_evt);
		},

		fade_in: function(tobj, display){
			tobj.style.opacity = 0;
			tobj.style.display = display || "block";

			(function fade() {
				var val = parseFloat(tobj.style.opacity);
				if (!((val += .05) > 1)) {
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
		if(n === null || n === undefined){
			return page_collector.pagedatas;
		}
		// first deal with short way of readding:
		if(pg === undefined && v === undefined){
			let n1 = page_collector.cur_page + '_' + n;
			return page_collector.pagedatas[n1] === undefined?page_collector.pagedatas['_' + n]:page_collector.pagedatas[n1];
		}
		let n2;
		if(pg){
			n2 = pg + '_' + n;
		}else if(pg === null || pg === '_'){
			// sepcial: get top_class value; and v is null as well
			// when get top class value: $(n,null,null) and $(n) is current page value
			n2 = '_' + n;
			v = (v == null?undefined:v);
		}else{
			n2 = page_collector.cur_page + '_' + n;
		}
		if(v === null){
			return page_collector.pagedatas[n2];
		}else if(v === undefined || v === '$del'){
			delete page_collector.pagedatas[n2];
			return true;
		}else{
			page_collector.pagedatas[n2] = v;
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
				let nn = e.target.nodeName;
				if(pckey && (nn==='INPUT' || nn==='SELECT')){
					let $o = this.triggers[pckey];
					if($o.value === undefined || $o.value.Join){
						$o.preval = $o.value;
						$o.value = e.target.value;
					}else{
						$o.value[e.target.name || 'default'] = e.target.value;
					}
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
					if(thefor){
						let forstr = '';
						$env[thefor[1]].forEach((_,i)=>{forstr += thefor[2].replace(/\$\{/, '${$env.' + thefor[1] + '[' + i + '].')});
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
			// if binds multi value to targets, use name attribute as key to store each value
			// take the value by 'key.name'
			let skeys = key.split('.'),pkey,skey;
			if(skeys[0]){
				pkey = skeys[0];
				skey = skeys[1];
			}else{
				pkey = skey[1];
			}
			let $_ = $t[pkey];
			if($_){
				if(!target){
					return $_.value;
				}
				if(target && ext){
					// reset with new setting
					$_.value = ext;
					return;
				}
				let data = target,mode = $_.mode;
				if(typeof($_.target)=== 'function'){
					return $_.target(pkey, $v);
				}else if(typeof($_.target)!=='string'){
					console.error("trigger target should be func or string");
				}
				let dom;
				try{
					dom = $c.querySelector('#' + $_.target) || $c.querySelectorAll($_.target);
				}catch(e){
					dom = $c.querySelectorAll($_.target);
				}
				if(!dom){
					try{
						dom = document.querySelector('#' + $_.target) || document.querySelectorAll($_.target);
					}catch(e){
						dom = document.querySelectorAll($_.target);
					}
				}
				if(dom){
					if(!dom.length){
						dom = [dom];
					}
					dom.forEach((d,i)=>{
						switch(mode){
							//case 'value':if(d.value !== undefined && d.value !== null){d.value=data};break;
							case 'value':{
								// handle value for inputs with name: value: {name: val}
								if(!skey || (skey && d.name === skey)){d.value=data}
							};break;
							case 'text':d.textContent=data;break;
							case 'dataset':if(pkey!=='pckey'){d.dataset[pkey]=data};break;
							case 'check':d.checked=data?true:false;break;
							case 'txtpl':{d.textContent=enver($_.value, data)};break;
							case 'innertpl':d.innerHTML=enver3($_.value, data);d.dataset.pckey=key;break;
							default:{
								if(d[$_.mode]){d[$_.mode]=data};
							}
						}
					});
				}else{
					console.error("dom not found");
				}
			}else{
				// add item
				if(typeof(target)==='string'){
					try{
						doms = $c.querySelector('#' + target) || $c.querySelectorAll(target);
					}catch(e){
						doms = $c.querySelectorAll(target);
					}
					if(!doms){
						return;
					}else if(!(doms instanceof NodeList)){
						doms = [doms];
					}
					let okdoms = [];
					doms.forEach((dom,i)=>{
						if(dom){
							if(dom.dataset.pckey===key){
								return;
							}
							okdoms.push(dom);
							if((dom.nodeName==='INPUT' || dom.nodeName === 'SELECT') && mode === 'value'){
								dom.addEventListener('change', $evt_chg);
								if(ext){dom.value=ext};
							}else if(dom.type === 'radio' || dom.type === 'checkbox'){
								dom.addEventListener('click', $evt_ipt_clk);
								if(ext){dom.checked=true};
							}else if(mode==='text'){
								dom.textContent = ext;
							}
							dom.dataset.pckey = key;
						}
					});
					if(okdoms.length<=0){
						return false;
					}else if(okdoms.length>1){
						this.triggers[key] = {target: target, mode: mode, preval: null, value: {}};
					}else{
						this.triggers[key] = {target: target, mode: mode, preval: "", value: ext};
					}
				}else if(typeof(target)==='function'){
					this.triggers[key] = {target: target, mode: 'function', value: null, preval: null}
				}
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
			return method.apply(this.inner_funcs, arguments);
		},
  };
  window.page_collector = page_collector;
	window.$pc = page_collector;
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
  data_store: {},
  passive_chain: {},
  timeout: 3000,
	ext_values: {},
  inner_funcs: {},
	curdlg : '',
	dlgs : {},
	/*
	dlg pattern: {dlgname: {
		did(string:id of dialog), 
		fid(string: id of form), 
		sma(function: submit function, arg0=dlgid, should return true),
		smb(string: submit button),
		clrb(string: clear button),
		spa(function: post dialog callback function, arg=rsp)
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

  getdlg: function(dlgname, toshow, title, itemid){
    //  check exists and ini for source for select input
    var dlgname = dlgname || dlg_mgm.curdlg;
    // could be dlgid
    var dlg = dlg_mgm.dlgs[dlgname];
	  if(!dlg){
      var ncd = '#' + dlg;
      for(var n in dlg_mgm.dlgs){
        if(ncd === dlg_mgm.dlgs[n].did){
          var dlg = dlg_mgm.dlgs[n];
          dlgname = n;
          break;
        }
      }
      if(!dlg){
        console.warn('not found dialog with name:' + dlgname);
        if(dlg_mgm.dlgs[dlgname]){
          delete dlg_mgm.dlgs[dlgname];
        }
        return null;
      }
    }
    if (itemid){
      // if set the itemid, will return the item of dialog
      return document.querySelector(itemid);
    }
    // could be undefined
    dlg_mgm.curdlg = dlgname;
    // ini the select options if exists
    // if(act==='create' && typeof(dlg_mgm.former) === 'object'){
      //  create form: use former function as a plugin
    //   dlg_mgm.former(dlg.fid, 'initial', inidata);
    if(title){
      let $titem = dlg.tid?$(dlg.tid):$(dlg.did).find(".modal-title");
      $titem.text(title);
    }
    if(toshow && $(dlg.did).hasClass('modal')){
      $(dlg.did).modal('show');
    }
    return dlg;
  },
  
  _set_select: function(dlg_id, sitem, url_or_data, force){
     // new version, sitem: itme name or item class;
     // return data should:
     // {targetname, data: [{label, value}, {label, value}, ...]}
    //let s_item = document.getElementById(dlg_id).querySelector('[name=' + sitem + ']');
		let s_item = $("#" + "dlg_id").find('[name=' + sitem + ']');
    if (!s_item){
      console.error("not found select item!");
    }
    if (!force && s_item.children().length > 0){
      return;
    }
		let opdata;
		if(typeof(url_or_data) === "string"){
			$.getJSON(url_or_data, function(rsp){
				if(rsp.data){
					opdata = rsp.data;
				}else{
				return;}
			});
		}else{
			opdata = url_or_data;
		}
		s_item.empty();
		for(let o,i=0,len=opdata.length;i<len;i++){
			o = opdata[i];
			s_item.append(`<option value="${o.value}">${o.title}</option>`);
		}
  },

  //binding input/select/radio/checkbox with attribute name to an object which stored in data_store
  //when dialog on change, react to object
  bind_vars: function(dlgname, act){
    var $tform = $(dlg_mgm.getdlg(dlgname).fid);
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

  set_passive_chain: function(dlgname, chains){
    // chains: {set_name: {passive_name1: change_mode1, passive_name2: change_mode2...}}
    var store = dlg_mgm.passive_chain;
    $tform = $(dlg_mgm.getdlg(dlgname).fid);
  },

  set_values: function(dlgname, vars_data, show, title, sva, clear){
    //c_or_l: clear: when a target with[name] without a vars_data[name], if set clear will clear the value
  	var dlg = dlg_mgm.getdlg(dlgname);
    var ttype, vval;
    var c = 0;
    var $tform = $(dlg.fid) || $(dlg.did);
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
    var f = sva || dlg.sva;
    if(typeof(f)==='function'){
      console.log('sva_func');
      f($tform, vars_data);
    }
    if(typeof(title) === 'string'){
      let titler = $(dlg.tid);
	  if (titler.length !== 1){
		  titler = $(dlg.did).find(".modal-title");
	  }
	  titler.text(title);
    }
    if(show && $(dlg.did).hasClass('modal')){
      $(dlg.did).modal('show');
    }
  },

  do_clear: function(dlgname, bynames, exact){
    var dlg = dlg_mgm.getdlg(dlgname);
    var tform = $(dlg.fid);
    if(tform.length !== 1){
      return;
    }
    if(!(bynames instanceof Array)){
      tform.find('[name]').each(function(){
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
      tform.find('[name]').each(function(){
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
		// you can do something after clear
		if(typeof(exact) === 'function'){
			exact(tform);
		}
  },

  //json removed
  get_json: function(did, item_names, item_mode, sp_ids, fillvals, skip_space){
    var gv = function(ipt){
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
    var tform = $(did).find("form");
    if(tform.length !== 1){
      tform = $(did);
    }
    var rta = {};
    var imode = 0;//0:default;1:item_name to collect;2:item_name to remove
    if($.isArray(item_names) && item_mode !== '-'){
      for(var i=0,len=item_names;i<len;i++){
        rta[item_names[i]] = null;
      }
      imode = 1;
    }else{
      tform.find('[name]').each(function(){
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
        tv = tform.find('#' + v).text();
        if(tv){rta[v] = tv}
      });
    }
    return rta;
  },

  post_form: function(dlgname, post_data, url, datatype, spa){
    //
    var dlg = dlg_mgm.getdlg(dlgname);
    if(!dlg){return}
    var url = url || ($(dlg.fid) || $(dlg.did).find("form")).attr('action');
    //specal data to post
    if(!post_data){
      var post_data = dlg_mgm.get_json(dlgname);
    }
    $.ajax({
      timeout: dlg_mgm.timeout,
      type: 'post',
      url: url,
      data: post_data,
      dataType: datatype || 'json'
    }).success(function(result){
      var spa = spa || dlg.spa;
      if(typeof(spa) === 'function'){
        spa(result);
      }else if(typeof(result)==='string'){
        alert('done_post: ' + result);
      }else{
        alert('post done!');
      }
    }).fail(function(jqXHR, textStatus, errorThrow){
      console.warn(textStatus);
    });
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
          if(v && i%2===1){rts += (values[v] || '')}else{rts += v}});
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

  ez_validate: function(form_or_datas, checkrs, alert){
		// set a css name: has-error to show error element, like: border-color: red
    var vali_regs = {
      number: /^-?\d+$/,
			date: /^\d{4}(\-)\d{1,2}\1\d{1,2}$/,
      phone: /^1[3|4|5|8][0-9]\d{4,8}$/,
      email:  /^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/,
      chinese: /^[\u0391-\uFFE5]+$/,
      english: /^[A-Za-z]+$/,
			idnum: /^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
    }
    var ichkr = function(value, cks){
      var ckrts = true,rt,ck;
      for(var i=0,len=cks.length;i<len;i++){
        ck = cks[i];
				if (ck === 'require'){
					rt = value?true:false;
				}else if (ck.indexOf(':')>0){
					var tokens = ck.split(':');
					switch(tokens[0]){
						//st: small than, lt: larger than; "require,LE:0,SE:100" .etc
						// how about: 'require,>=0,<=100'
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
			var ckr=checkrs?(checkrs[tn] || this.getAttribute('validate')):this.getAttribute('validate');
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

  go_submit: function(dlgname, sma, post_data, rtype, sp_post, validate, chkr){
    // rtype: 'text', 'json', 'xml', ....
    var dlg = dlg_mgm.getdlg(dlgname);
    var rtype = rtype || 'json';
    if(validate && !dlg_mgm.ez_validate(dlg.fid, chkr, true)){
			alert("输入内容有误请检查!");
      return false;
    }
    // if(!$(dlg.fid).valid()){
    //   return false;
    // }
    var f = typeof(sma) === 'function'?sma:dlg.sma;
    if(f && !f($(dlg.did))){
      console.error("SMA in DIALOG: " + dlgname + " IS ERROR!");
			return false;
      //f();
    }else{
      var post_data = post_data || dlg_mgm.get_json(dlg.fid);
      if($.isPlainObject(sp_post)){
        $.extend(post_data, sp_post);
      }
      dlg_mgm.post_form(dlgname, post_data, '', rtype);
    }
    if($(dlg.did).hasClass('modal')){
      $(dlg.did).modal('toggle');
    }
    if(typeof(dlg.doclear) === 'function'){dlg.doclear()}
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

    setpagedata: function(tbl_id, key, val){
      if(!page_bar.pagedatas[tbl_id]){
        page_bar.pagedatas[tbl_id] = {key: val};
        return page_bar.pagedatas[tbl_id];
      }else{
        if(key === null){
          delete page_bar.pagedatas[tbl_id];
        }else if(key === undefined){
          return page_bar.pagedatas[tbl_id];
        }else if(typeof(key)==='object'){
          page_bar.pagedatas[tbl_id] = key;
        }else if(!val){
          return page_bar.pagedatas[tbl_id][key];
        }else{
          page_bar.pagedatas[tbl_id][key] = val;
          return page_bar.pagedatas[tbl_id][key];
        }
      }
    },
    
    del_rows: function(div, start, length){
      let $tobj = $('#' + (div || page_bar.curdiv));
      let $trows = $tobj.find("> tbody >");
      // if length < 0, starts from bottom and ignore start; else start >= 0
      if (start > trows.length){
        return;
      }else if (start >= 0 && length > 0){
        // starts from top
        let rlength = Math.max(length, trows.length);
        for(let i=start;i<rlength;i++){
          trows[i].remove();
        }
      }else if (length < 0){
        // starts from bottom
        let rlength = Math.min(trows.length, Math.abs(length));
        for(let i=1;i<rlength;i++){
          trows[rlength - i].remove();
        }
      }
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
      const tbody = $(tbl_obj).find('tbody');
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
				rows[idx].remove();
			}
		}
		return idx;
	},
	
	add_row: function(tbl_obj, pos, rowdata, tmpl){
		const tbl = typeof(tbl_obj)==='object'?tbl_obj:document.getElementById(tbl_obj);
		let row_num = tbl.tBodies[0].rows.length;
		tmpl = tmpl===undefined?$(tbl_obj).data('stable').tmpl:tmpl;
		let prtmnt = $(tbl).data('stable')['prtmnt'];
		// headrow = 0; etc: pos_range=[1,20], row_num=21; insert pos=1:first;-1,>=21:last;
		if(row_num === 0){
			pos = 0;
		}else if(pos===0){
			pos = 1;
		}else if(pos === -1 || pos > row_num){
			pos = row_num + 1;
		}
		if(typeof(prtmnt)==='function'){
			row = prtmnt(rowdata);
		} else {
			row = rowdata;
		}
		let tr = tbody.insertRow(pos);
		tr.outerHTML = eval('`' + tmpl + '`');
	},

    del_rows: function(tbl_obj, row_th, count){
      if(row_th>=0){ 
        var tbody = $(tbl_obj).find('tbody')[0];
        var count = count || 1;
        if(count === 1){
          tbody.deleteRow(row_th);
        }else{
          while(count>0){
            tbody.deleteRow(row_th);
            count--;
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
            tbl_bar: '',
            tbl_pages: 0, // count page
            tbl_cur_page: 0, // current page
            tbl_offset: 0,  // 1->last item index
            page_limit: 20,
            autoload: true, //after initial load data immediatly
            prtmnt: null, // row-data-formating:(row_data)=>{return new-row_data}
            pagedata: null,
            after_gopage: null,
			selections: null,
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
			tdata['selection'] = tdata.pagedata[this.rowIndex - 1];
			this.classList.add('active');
			if(event.data.act){
				event.data.act(tdata['selection']);
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
          methods['go_page'](1, true, null, true, tbl_obj);
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
    
    set_page_data: function(pagedata, iniobj, tmpl){
		//for debugging
		let tbl_obj = iniobj?$(iniobj):$(this);
		let cursetting = tbl_obj.data('stable');
		//console.log(cursetting);
		tmpl = tmpl?tmpl:cursetting['row_tmpl'];
		//tbl_funcs.clear(tbl_obj);
		tbl_funcs.setrows(tbl_obj, tmpl, pagedata, cursetting['prtmnt']);
		if(cursetting['tbl_bar']){
			page_bar.assign(cursetting['tbl_bar']).create(null, 1);
		}
		cursetting['tbl_pages'] = 1;
		cursetting['pagedata'] = pagedata;
	},
		
	set_row: function(rowidx, rowdata, prtmnt, tmpl){
		//idx = 0 ->
		let tbl_obj = $(this);
		tmpl = tmpl===undefined?tbl_obj.data('stable').row_tmpl:tmpl;
		prtmnt = prtmnt===undefined?tbl_obj.data('stable').prtmnt:prtmnt;
		let row = prtmnt(rowdata);
		if (!row){
			return false;
		}
		tbl_obj.find('tbody')[0].rows[rowidx-1].outerHTML =  eval('`' + tmpl + '`');
		return row;
	},

	del_row: function(start, len){
		if(start<0){
			return false;
		}
		var max = this.tBodies[0].rows.length;
		len =  max - len - start > 0?len:max - start;
		tbl_funcs.del_rows(this, start, len);
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
		
	rowid_del: function(rowid){
		$(this).find("tr[rowid=" + rowid + "]").remove();
	},
	
	append_row: function(rowdata){
		tbl_funcs.add_row(this, -1, rowdata);
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
			}
			// if(cursetting['extkeys']){
			//   $.extend(allparam, cursetting['extkeys']);
			// }
			params = params || cursetting['filter_params'];
			if(params){
				$.extend(allparam, params);
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
			}else if(rt.respon && rt.respon === 'failure'){
				console.error("failure get data!");
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
					page_bar.create(cursetting['tbl_bar'], cursetting.tbl_pages);
					page_bar.set_page(cursetting['tbl_bar'], pagenum, cursetting.tbl_pages);
				}
			}
			cursetting['pagedata'] = data;
			tbl_funcs.setrows(tbl_obj, cursetting['row_tmpl'], data, cursetting['prtmnt']);
			cursetting['tbl_offset'] = cursetting['tbl_cur_page'] * cursetting['page_limit'] + data.length;
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



dlg_mgm._ = dlg_mgm.getdlg;