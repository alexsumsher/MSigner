var _litevars = {
	cur_page: null,
	pagedatas: {},
	triggers: {},
	PG: function(pgid){
		this.cur_page = pgid;
		return this;
	},
	$$:function (key, target, mode, ext){
		// to dom object: data-pckey="key"
		// mode0: key => get value
		// mode1: key, target as data to set
		// mode2: key, target, mode, ext as data
		// trigger_obj:
		// string=>querySelector(s)
		// function => apply ($v => page_collector.$(thispage)
		// store: key: {target, mode, value, preval}
		// + next ver: batch mode: key is data-object with setter/getter; {key:value}
		// + for page seperate: (update 20200306): triggers={pagename: {triggers}, ....}
		mode = mode || 'value';
		let $c = document.getElementById(this.cur_page) || document;
		if(!$c){
			return false;
		}
		// $v: get value from pagedatas
		const $v = (n, v)=>{
			n = this.cur_page + '_' + n;
			if(!v){
				return this.pagedatas[n];
			}else{
				this.pagedatas[n] = v;
			}
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
		
		//let $t = this.triggers;
		let $t = this.triggers[this.cur_page];
		if (!$t){
			 this.triggers[this.cur_page] = {};
			 $t= this.triggers[this.cur_page];
		}
		let $_ = $t[key];
		if($_){
			if(target === undefined){
				if ($_.mode === 'text'){
					return document.querySelector($_.target).textContent || $_.value;
				}
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
						case 'value':{
							if(dom.nodeName === "SELECT"){
								for(let _i=0,_l=dom.options.length;_i<_l;_i++){
									if(dom.options[_i].value == data){
										dom.selectedIndex = _i;
										dom.value=data;
										break;
									}
								}
							} else {
								dom.value=data;
							}
							$_.value = data;
						};break;
						case 'text':dom.textContent=data;$_.value = data;break;
						case 'dataset':if(key!=='pckey'){dom.dataset[key]=data};break;
						case 'check':dom.checked=data?true:false;break;
						case 'txtpl':{dom.textContent=enver($_.value, data)};break;
						case 'innertpl':dom.innerHTML=enver3($_.value, data);break;//dom.dataset.pckey=key;
						default:{
							if(dom[$_.mode]){dom[$_.mode]=data};
						}
					}
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
						if((nodename==='INPUT' || nodename === 'SELECT' || nodename==="TEXTAREA") && mode === 'value'){
							//dom.addEventListener('change', $evt_chg);
							if(ext){dom.value=ext};
						}else if(dom.type === 'radio' || dom.type === 'checkbox'){
							//dom.addEventListener('click', $evt_ipt_clk);
							if(ext){dom.checked=true};
						}else if(mode === 'txtpl' || mode === 'innertpl'){
							//pass
						}else{
							// auto reset mode to text
							mode = 'text';
							if(typeof(ext)==='string'){dom.textContent = ext;}
						}
						dom.dataset.pckey = key;
					}
				});
				if(okdoms.length<=0){
					console.log("no ok dom");
					return false;
				} else if (okdoms.length === 1){
					$t[key] = {target: seler, mode: mode, value: ext};
				} else {
					$t[key] = {target: okdoms, mode: mode, value: ext};
				}
			}else if(typeof(target)==='function'){
				$t[key] = {target: target, mode: 'function', value: null}
			}
			return $t[key];
		}
	},
}