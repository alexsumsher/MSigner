// page vendor
// 处理页面相关的数据

var _back_datar = (function(){
	// 加载系数据,生成基础工作环境
	return {
		
	}
})();

const d_cmds = {
	commanders: [],
	create_meeting: function(params, callback){
		axios.request({
			url: '/api/meeting?action=new',
			method: 'post',
			data: params,
			headers: {"Content-Type": 'application/x-www-form-urlencoded'},
			transformRequest: [function (data) {
				let ret = ''
				for (let it in data) {
				  ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
				}
				return ret
			  }],
		}).then((rsp)=>{
			if(rsp.data.success==='yes'){callback(rsp.data.data)}
		});
	},
	set_attenders: function(params, callback){
		axios.request({
			url: '/api/attenders?action=add',
			method: 'post',
			data: params,
			headers: {"Content-Type": 'application/x-www-form-urlencoded'},
			transformRequest: [function (data) {
				let ret = ''
				for (let it in data) {
					if (data[it] instanceof Array){
						// attenders
						data[it].forEach((a,i)=>{
							if (typeof(a)==='string' || typeof(a) === 'number'){
								ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
								return;
							}
							for (let k in a){
								ret += encodeURIComponent(it) + "[" + i + "][" + k + "]=" + encodeURIComponent(a[k]) + "&";
							}
						});
						continue
					}
				  ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
				}
				console.log(ret);
				return ret
			  }],
		}).then((rsp)=>{
			if(rsp.data.success==='yes'){callback(rsp.data.data)}
		});
	},
	kick_attender: function(params, callback){
		// {mid: _PGC.$("cur_meeting"), aid: row.aid}
		axios.request({
			url: '/api/attenders?action=delete',
			method: 'post',
			data: params,
			headers: {"Content-Type": 'application/x-www-form-urlencoded'},
			transformRequest: [function (data) {
				let ret = ''
				for (let it in data) {
				  ret += encodeURIComponent(it) + '=' + encodeURIComponent(data[it]) + '&'
				}
				return ret
			  }],
		}).then((rsp)=>{
			if(rsp.data.success==='yes'){callback(rsp.data.data)}
		});
	},
	_xyz: 0,
	load_departments: function(){
		axios.request({url: "/school", method:'get',  params: {userid: 'alex', objectid: '2XaxJgvRj6Udone', action: 'developments'}}).then((rsp)=>{
			rsp = rsp.data;
			if (rsp && rsp.data){
				_departments = rsp.data;
				// for set 建立映射部门-名称
				let _dps = [..._departments];
				let n = _dps.shift(), c = 0;
				while(n){
					if (c > 300){
						break;
					}
					_dpmap[n.departid] = n.departname;
					if (n.child){
						_dps.push(...n['child']);
					}
					n = _dps.shift();
				}
			}
		});
	},
};

const _input_checker = function(vname, value, ...ext){
	console.log(ext);
	// 统一检验输入数据正确性;只做必要的部分
	const is_plainobj = function(obj){
		if (obj === null || obj === undefined){
			return false;
		}
		return Object.getPrototypeOf({}) === Object.getPrototypeOf(obj);
	};

	if (is_plainobj(vname)){
		//pass
		let output = true;
		for(let k in vname){
			output = output && main_checker(k, vname[k]);
		}
		return output
	}
	let rt;
	let regx;
	switch(vname){
		case 'p_start':
		case 'p_end':
		case 'period':
		{
			if (ext.length === 0){
				// check single
				rt = !isNaN(new Date(value).getDate());
			}else{
				// compare date: value-pstart, ext[0]-pend
				rt = new Date(value) < new Date(ext[0]);
			}
		};break;
		case 'm_ontime':rt = value.match(/\d{1,2}[\:：\s]\d{2}/) !== null;break;
		default: rt = true;
	}
	if (rt === undefined && regx && typeof(value) === 'string'){
		rt = value.match(regx);
	}
	return rt;
};

var _page_helper = {
	_seled_roomid: 0,
	_seled_roomname: '',
	_seled_room: null,
	room_seler: function(win, params){
		// 加载会议室数据，根据日期和时间选择
		const setval = function(win, v_id, v_name){
			return ()=>{win.m_roomid = v_id; win.m_roomname = v_name};
			//win.m_roomid = _page_helper._seled_roomid;
			//win.m_roomname = _page_helper._seled_roomname;
		}
		axios.request({url: "/resource/mroom", method:'get', params: params}).then((rsp)=>{
			data = rsp.data;
			if (data.success === 'no'){return}
			const setval = function(win, v_id, v_name, v_smode){
				return ()=>{win.m_roomid = v_id; win.m_roomname = v_name; win.m_signmode = v_smode};
			}
			let btns = {};
			data.data.forEach((n)=>{
				btns[n.name] = setval(win, n.roomid, n.name, n.sign_mode);
			});
			$actionSheet.show({
				// 支持三种主题样式 ios/android/weixin
				theme: 'weixin',
				title: '会议室选择',
				buttons: btns,
			});
		});

	},
	mtype_seler: function(win, params){
		$actionSheet.show({
			// 支持三种主题样式 ios/android/weixin
			theme: 'weixin',
			title: '会议类型',
			buttons: {
				// 操作列表选项文字及回调函数
				'按周重复': () => {
					win.m_type = 1;
					win.m_typename = "按周重复";
				},

				'按月重复': () => {
					win.m_type = 2;
					win.m_typename = "按月重复";
				}
			}
		});
	},
	// others
};