// admin index js
var _env = {
	default_signpre: 10,
	default_signlimit: 30,
	schoolid: '', //objid
	username: "", // 无法穿透session，获取sessionStorage的数据，只有username可用
	userid: "",
};
var _departments = null; // 全校部门-教师
var _dpmap = new Set();

var imsger = new $.zui.Messager('', {type: 'primary', time: 3000, icon: 'icon-bolt'});
var emsger = new $.zui.Messager('', {type: 'danger', time: 3000, icon: 'icon-warning-sign'});

// PART of local_page_functions
FUNCS = {
	dpdata2ul: function(){
		if (!_departments){
			emsger.show("无部门数据");
			return false;
		}
	},
	compare: function(o1, o2){
		let changed = {};
		for(k in o1){
			if (o1[k] != o2[k]){
				changed[k] = o2[k];
			}
		}
		return changed;
	},
	date_check: function(d1, d2){
		//确认日期的合理性
		// 只有d1，则判断d1是否>=今日
		// d1,d2: 判断d1和d2至少差距一日，且d2>d1
	},
	switch_rpmode: function(rpv){
		let show=0,hide=2;
		if (rpv == 0){
			show = 0;
			hide = 2;
		}else {
			show = 2;
			hide = 0;
		}
		page.querySelectorAll(".mode" + show).forEach((n)=>{n.style.display='table'});
		page.querySelectorAll(".mode" + hide).forEach((n)=>{n.style.display='none'});
		_PGC.$("rpmode", rpv, "meeting_create");
	},
	data_convert: function(source, mapper){
		//将来源数据转换为可以在UL_TREE中显示的格式
		/*
		source: {departid, departname, departcode, child:[]}
		mapper: {title, url, html, children, open, id}
		*/
		let outer = [];
		const convert = (obj, _title, _id, _child)=>{
			//console.log(obj);
			let output = {title: obj[_title], id: obj[_id], level: obj['level']};
			if (obj[_child]){
				output.children = [];
				obj[_child].forEach((n)=>{
					output.children.push(convert(n, _title, _id, _child));
				});
			}
			return output;
		};
		let _title = mapper['title'],
			_id = mapper['id'],
			_child = mapper['child'];
		
		if (_exec.is_plainobj(source)){
			outer.push({title: source[_title], id: source[_id], level: source['level'], children: []});
			source = source[_child];
		}
		source.forEach((n)=>{
			outer.push(convert(n, _title, _id, _child));
		});
		//console.log(outer);
		return outer;
	},
	load_departments: function(callback){
		//加载部门
		// 测试数据,不通过智慧校园端访问
		$.getJSON(_exec.make_urlparam({userid: 'alex', objectid: '2XaxJgvRj6Udone', action: 'developments'}, "/school"), function(rsp){
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
				if (typeof(callback) === 'function'){
					callback();
					// display in tree
				}
			}
		});
	},
	load_dpart_users: function(dpid, callback){
		if (typeof(callback) == 'function'){
			callback();
		}
	},
}

// PART of PAGER
page_initor('meeting', function(){
	// comon
	if (!_departments){
		FUNCS.load_departments();
	}
	if (serverdata){
		_env.userid = serverdata.userid;
	}
	// 选择部门列表中的部门项目
	let dlg_dp = document.getElementById("dlg_departments");
	let dom_ul = document.getElementById("depart_tree2");
	dom_ul.onclick = function(evt){
		let li = evt.target.parentElement;
		if (li.tagName !== 'LI'){
			return;
		}
		let dpid = li.dataset.id;
		let url;
		if (_PGC.cur_page === 'attenders'){
			let userby = _PGC.$("userby");
			if (userby === "all" || userby==="school"){
				url = _exec.make_urlparam({action: 'dpart_users', departid: dpid, level: 6}, "/school");
			} else if (userby === 'imported'){
				url = _exec.make_urlparam({action: 'list', departid: dpid, page: 1, size: 100}, "/resource/users");
			} else if (userby === 'reged'){
				url = _exec.make_urlparam({action: 'list', departid: dpid, page: 1, size: 100, onlyreged: 'yes'}, "/resource/users");
			} else {
				console.warn("unknown require");
				return;
			}
		} else {
			url = _exec.make_urlparam({action: 'dpart_users', departid: dpid, level: 6}, "/school");
		}
		// show loading
		dlg_dp.classList.add("loading");
		//let url = _exec.make_urlparam({action: 'dpart_users', departid: dpid, level: 6}, "/school");
		$.getJSON(url, function(rsp){
			dlg_dp.classList.remove("loading");
			
			let seler = document.getElementById("users_in_dpart");
			if (rsp && rsp.data){
				let userby = _PGC.$("userby"),namekey;
				if (userby === "all" || userby==="school"){namekey="name"}else{namekey="username"}
				_exec.set_sel_opts_ex(seler, rsp.data, null, namekey, 'userid', ['uid', 'wxuserid','departid', 'cellphone']);
			} else{
				//清空
				emsger.show("该部门无用户");
				seler.options.length = 0;
			}
			// active 效果；单行
			let act_span = li.children[0];
			if (_PGC.$("act_span")){_PGC.$("act_span").classList.toggle("seled")}
			_PGC.$("act_span", act_span);
			act_span.classList.toggle("seled");
		});
	};
	// 全选/取消全选
	dlg_dp.querySelector("#btn_sels_all").onclick = function(e){
		let seler = dlg_dp.querySelector("#users_in_dpart");
		let opts = seler.options;
		for(let i=0,len=opts.length;i<len;i++){
			opts[i].selected = true;
		}
		seler.focus();
	}
	dlg_dp.querySelector("#btn_unsel_all").onclick = function(e){
		let seler = dlg_dp.querySelector("#users_in_dpart");
		let opts = seler.options;
		for(let i=0,len=opts.length;i<len;i++){
			opts[i].selected = false;
		}
	}
	// 打开dlg即清空右侧
	$("#dlg_departments").on("shown.zui.modal", function(){
		document.getElementById("users_in_dpart").options.length=0;
	});
	// 筛选
	document.getElementById("meeting_fresh").addEventListener("click", function(evt){
		$("#meeting_tbl").stable("go_page", 1, null, null, true);
	});
});

page_collector.bind_ini("meeting", function(){
	// ini 
	_PGC.$("m_dlg_mode", 'new');
	_PGC.$$("dlg_minfo", '#dlg_meetinginfo .modal-body', 'stpl', '<h5>会议名称：${name}</h5><ul><li>人数上限：${allow_people}</li><li>会议室：${roomname}</li><li>签到序列号${room_identifier}</li><li>时间：${nextdtime}</li><li>时段：${p_start}</li><li>时段尾：${p_end}</li><li>（周期）日期：${rparg}</li><li>时长：${mtime}</li></ul>');
	// TABLE
	$("#meeting_tbl").stable({
		source_url: '/resource/meeting?action=mlist', 
		filter_params: {holder: 'yes', userid: _env.userid},
		tbl_bar: '#meeting_bar',
		key_name: 'mid',
		last_id: 0,
		page_limit: 20,
		autoload: true,
		pagedata: [],
		filter_zoom: '#meeting_filter',
		prtmnt: (r)=>{
			if(r.rpmode == 0){
				r.rpmode_txt = "一次性会议";
			}else if (r.rpmode == 1){
				r.rpmode_txt = "周期(周)会议";
			} else if (r.rpmode == 2){
				r.rpmode_txt = "周期(月)会议";
			}
			let r_pre = r.sign_pre || _env.default_signpre,
				r_limit = r.sign_limit || _env.default_signlimit;
			r.sign_txt = "会前[" + r_pre + "(分钟)], 最迟[" + r_limit + "(分钟)]";
			return r;
		},
		row_tmpl: '<tr rownum="${row.mid}"><td>${row.name}</td><td>${row.rpmode_txt}</td><td>${row.roomname}</td><td>${row.nextdtime}</td><td>${row.mtime}</td><td>${row.sign_txt}</td><td><button class="btn btn-sm act1" type="button">修改</button><button class="btn btn-sm act2" type="button">详情</button><button class="btn btn-sm act3" type="button">人员</button><button class="btn btn-sm act4" type="button">x</button></td></tr>',
		innerbtn_actions: [
			['编辑', 'act1', function(r){
				// over time, over status
				let mid = r.getAttribute('rownum');
				let sdata = $("#meeting_tbl").data("stable").selections;
				if(sdata.rpmode === 0 && (new Date(sdata.nextdtime) < new Date())){
					alert("会议已经过期");
					return;
				}
				_PGC.$("cur_meeting", mid, 'meeting_create');
				if(mid != $("#meeting_tbl").data("stable").selections.mid){
					_PGC.$("cur_meetingdata", $("#meeting_tbl").data("stable").pagedata[mid], "meeting_create");
				}else {
					let time = sdata['ontime'];
					if (time.length > 5){
						time = time.substr(0, time.length-3);
						if (time.length<5){
							time = '0' + time;
						}
						sdata['ontime'] = time;
					}
					// p_star/p_end
					if (sdata.p_start){
						sdata.p_start = sdata.p_start.substr(0, 10);
					}
					if(sdata.p_end){
						sdata.p_end = sdata.p_end.substr(0, 10);
					}
					_PGC.$("cur_meetingdata", sdata, "meeting_create");
				}
				//_PGC.$("work_mode", "modify", 'meeting_create');
				go_page("meeting_create", {work_mode: "modify"});
			}],
			['详情', 'act2', function(r){
				let mid = r.getAttribute('rownum');
				$.getJSON("/resource/meeting?action=full_detail&mid=" + mid, function(rsp){
					if(rsp && rsp.success==='yes'){
						//alert(JSON.stringify(rsp.data));
						$("#dlg_meetinginfo").modal({show:true});
						_PGC.$$("dlg_minfo", rsp.data);
					}else{
						emsger.show("无法加载");
					}
				});
			}],
			['参会人员', 'act3', function(r){
				let rdata = $("#meeting_tbl").data("stable").selections;
				_PGC.$("cur_meeting", rdata.mid, "attenders");
				_PGC.$("cur_meeting_name", rdata.name, "attenders");
				_PGC.$("cur_meeting_counting", rdata.counting, "attenders");
				go_page("attenders");
			}],
			['删除', 'act4', function(r){
				if (!confirm("确定删除？不能恢复!")){return;}
				let rdata = $("#meeting_tbl").data("stable").selections;
				$.post("/api/meeting?action=delete", {mid: rdata.mid, mcount:rdata.counting}, function(rsp){
					if (rsp && rsp.success === 'yes'){
						imsger.show("成功");
						$("#meeting_tbl").stable("go_page", 1, null, null, true);
					} else if(rsp && rsp.msg !== 'done'){
							alert(rsp.msg);
					}
				}, 'json');
			}],
		]
	});
	// UI ACTIONS
	document.getElementById("meeting_add").onclick = function(){
		_PGC.$("addnew", null);
		_PGC.$("cur_meeting", 0, 'meeting_create');
		_PGC.$("work_mode", 'new', 'meeting_create');
		go_page("meeting_create");
	}
});
page_collector.bind_load("meeting", function(){
	if (_PGC.$('work_mode', undefined, 'meeting_create') === 'new' && _PGC.$("addnew") === 'success'){
		let mdata = _PGC.$("cur_meetingdata", undefined, "meeting_create");
		if (mdata.mid){
			$("#meeting_tbl").stable('insert_row', 1, mdata);
		}
		// then clear
		_PGC.$('work_mode', null, 'meeting_create');
	}
});

page_collector.bind_ini("mroom", function(){
	// ini 
	_PGC.$("m_dlg_mode", 'new');
	// TABLE
	$("#mroom_tbl").stable({
		source_url: '/resource/mroom?action=list', 
		filter_params: null,
		tbl_bar: '#mroom_bar',
		key_name: 'roomid',
		last_id: 0,
		page_limit: 20,
		autoload: true,
		pagedata: [],
		filter_zoom: '',
		prtmnt: (rowdata)=>{
			if (rowdata.sign_mode == 1){
				rowdata.sign_mode_txt = '支持';
			} else {
				rowdata.sign_mode_txt = '不支持';
			}
			if (!rowdata.next_meeting){
				rowdata.next_meeting = "";
			}
			if (!rowdata.next_mdtime){
				rowdata.next_mdtime = 0;
			}
			return rowdata;
		},
		row_tmpl: '<tr rownum="${row.roomid}"><td>${row.name}</td><td>${row.sign_mode_txt}</td><td>${row.room_identifier}</td><td>${row.allow_people}</td><td>${row.next_meeting}</td><td>${row.next_mdtime}</td><td><button class="btn btn-sm act1" type="button">修改</button><button class="btn btn-sm act2" type="button">时间表</button><button class="btn btn-sm act3" type="button">删除</button></td></tr>',
		innerbtn_actions: [
			['编辑', 'act1', function(r){
				// 修改会议室数据
				console.log("on edit");
				_PGC.$("m_dlg_mode", "modify");
				_PGC.$("m_dlg_roomid", r.getAttribute('rownum'));
				let sel_data = $("#mroom_tbl").data('stable')['selections'],
					pkey = $("#mroom_tbl").data('stable')['key_name'];
				if (sel_data[pkey] != r.getAttribute('rownum')){
					alert("wrong selection");
					return;
				}
				dlg_mgm._$dlg("mroom").url = '/api/mroom?action=modify';
				dlg_mgm.opendlg('mroom', sel_data, '编辑：' + sel_data['name']);
				// set for sign_mode:
				if (sel_data.sign_mode == 1){
					dlg_mgm._$dlg().find('[name="room_identifier"]').prop("disabled", false);
				} else {
					dlg_mgm._$dlg().find('[name="room_identifier"]').prop("disabled", true);
				}
			}],
			['时间表', 'act2', function(r){
				_PGC.$("sel_roomid", r.getAttribute('rownum'));
				_PGC.$("sel_roomn", r.cells[0].textContent);
				go_page("room_schedule");
			}],
		]
  });
	// UI ACTIONS
	document.getElementById("btn_addmroom").onclick = function(){
		dlg_mgm._$dlg("mroom").url = '/api/mroom?action=new';
		dlg_mgm.opendlg("mroom", null, '新增会议室', function(){
			// load and list departments
		});
	};
});

page_collector.bind_ini('attenders', function(){
	page_collector.$$("cmt", "#cur_meeting", 'txtpl', "当前会议：${mname}");
	page_collector.$$("mtshow", "#show_mtime", "text", "第0次");
	// TABLE
	// 注意兼容以前导致命名混淆：此处mtime并非meeting time（会议时长） 而是 meeting times（会议次数）
	$("#attenders_tbl").stable({
		source_url: '/resource/attenders?action=list', 
		filter_params: {mcount: 0},
		tbl_bar: '#attenders_bar',
		key_name: 'aid',
		last_id: 0,
		page_limit: 100,
		autoload: false,
		pagedata: [],
		filter_zoom: '',
		prtmnt: (r)=>{
			//aid,userid,username,roleid,signtime,status
			if(r.roleid === 1){
				r.role_txt = "管理员";
			}else if(r.roleid == 0){
				r.role_txt = "成员";
			} else {
				r.role_txt = "未知身份";
			}
			// if meeting.status=over
			switch(r.status){
				case 0:r.status_txt="未签到或缺席";break;
				case 1:r.status_txt="已签到";break;
				case 2:r.status_txt="签到-迟到";break;
				case 3: r.status_txt = "请假";break;
				default:r.status_txt="-";
			}
			return r;
		},
		after_gopage: (d)=>{},
		row_tmpl: '<tr rownum="${row.aid}"><td>${row.userid}</td><td>${row.username}</td><td>${row.role_txt}</td><td>${row.signtime}</td><td>${row.status_txt}</td><td><button class="btn btn-sm act1" type="button"><i class="icon icon-times"></i></button><button class="btn btn-sm act2" type="button"><i class="icon icon-hand-up"></i></button><button class="btn btn-sm act3" type="button">-</button></td></tr>',
		innerbtn_actions: [
			['删除', 'act1', function(r){
				let row = $("#attenders_tbl").data("stable")['selections'];
				if(!confirm("确定删除？")){
					return;
				}
				$.post("/api/attenders?action=delete", {
					mid: _PGC.$("cur_meeting"),
					aid: row.aid,
					mcount: $("#attenders_tbl").data('stable').filter_params.mcount
				}, function(rsp){
					if(rsp && rsp.success === 'yes'){
						imsger.show("删除成功！");
					}else{
						emsger.show("删除失败！");
						if (rsp.msg !== 'done'){
							alert(rsp.msg);
						}
					}
				}, 'json');
			}],
			['管理员', 'act2', function(r){
				let row = $("#attenders_tbl").data("stable")['selections'];
				let target_roleid;
				if(row.roleid === 1 && confirm("用户已经是管理员，是否要调整为普通用户？")){
					target_roleid = 0;
				}else if (row.roleid === 0 && confirm("用户调整为会议管理员？")){
					target_roleid = 1;
				}
				$.post("/api/attenders?action=role", {
					mid: _PGC.$("cur_meeting"),
					aid: row.aid, roleid: target_roleid,
					mcount: $("#attenders_tbl").data('stable').filter_params.mcount
				}, function(rsp){
					if(rsp && rsp.success === 'yes'){
						imsger.show("设置成功！");
						r.cells[2].textContent = target_roleid===1?"管理员":0;
					}else{
						emsger.show("设置失败！");
						if (rsp.msg !== 'done'){
							alert(rsp.msg);
						}
					}
				}, 'json');
			}],
			['取消请假', 'act3', function(r){
				
			}],
		],
	});
	// UI ACTIONS
	// 导入
	let dom_ul = document.getElementById("depart_tree2");
	this.querySelector("#btn_clear_all").onclick = function(){
		alert("危险操作，暂时屏蔽");
		return;
		if(!confirm("此操作将移除所有已加入成员，确定要这么做？")){
			return;
		}
		if(!_PGC.$("cur_meeting")){
			alert("未指定会议！");
			return;
		}
		$.post("/api/attenders?action=clear", {
			mid: _PGC.$("cur_meeting"),
			mtimes: -1,
			mcount: $("#attenders_tbl").data('stable').filter_params.mcount
		}, function(rsp){
			if(rsp && rsp.success === 'yes'){
				imsger.show("清除成功！");
				$("#attenders_tbl").stable('clear');
			}else{
				emsger.show("设置失败！");
			}
		}, 'json');
	}
	this.querySelector("#btn_sel_fromall").onclick = function(){
		// load depart-user data and open-show in dlg
		if (!_departments){
			return;
		}
		_PGC.$("userby", "school");
		if (dom_ul.children.length < 1){
			let dps = FUNCS.data_convert(_departments, {title: 'departname', id: 'departid', child: 'child'});
			$(dom_ul).data('zui.tree').reload(dps);
		}
		dlg_mgm.opendlg("choose_bydpart");
	}
	this.querySelector("#btn_sel_imported").onclick = function(){
		if (!_departments){
			return;
		}
		_PGC.$("userby", "imported");
		if (dom_ul.children.length < 1){
			let dps = FUNCS.data_convert(_departments, {title: 'departname', id: 'departid', child: 'child'});
			$(dom_ul).data('zui.tree').reload(dps);
		}
		dlg_mgm.opendlg("choose_bydpart");
	};
	this.querySelector("#btn_sel_reged").onclick = function(){
		if (!_departments){
			return;
		}
		_PGC.$("userby", "reged");
		if (dom_ul.children.length < 1){
			let dps = FUNCS.data_convert(_departments, {title: 'departname', id: 'departid', child: 'child'});
			$(dom_ul).data('zui.tree').reload(dps);
		}
		dlg_mgm.opendlg("choose_bydpart");
	};
	// 上一次/下一次会议
	document.getElementById("attenders_premeeting").addEventListener('click', function(evt){
		if (_PGC.$eq("cur_meeting_counting",0)){
			return;
		}
		let pm = $("#attenders_tbl").data('stable').filter_params;
		if (pm.mcount>1){
			pm.mcount--;
		} else {
			alert("已经是第一次会议");
			return;
		}
		$("#attenders_tbl").stable('go_page', 1, null, null, true);
		_PGC.$$("mtshow", "第" + pm.mcount + "次");
	});
	document.getElementById("attenders_nextmeeting").addEventListener('click', function(evt){
		if (_PGC.$eq("cur_meeting_counting",0)){
			return;
		}
		// if empty will not go: 注意inner HTML=“”
		let r0 = document.getElementById("attenders_tbl").tBodies[0].rows[0];
		let $tbl = $("#attenders_tbl");
		let pm = $tbl.data('stable').filter_params;
		if (pm.mcount >= _PGC.$("cur_meeting_counting")){
			alert("已经是最近会议");
			return;
		}
		if (r0 && r0.innerHTML !== ""){
			pm.mcount++;
			$tbl.stable('go_page', 1, null, null, true);
			_PGC.$$("mtshow", "第" + pm.mcount + "次");
		}
	});
	document.getElementById("attenders_curmeeting").addEventListener("click", function(evt){
		if (_PGC.$eq("cur_meeting_counting",0)){
			return;
		}
		let mcount_max = _PGC.$("cur_meeting_counting");
		if ($("#attenders_tbl").data('stable').filter_params.mcount < mcount_max){
			$("#attenders_tbl").stable('go_page', mcount_max, null, null, true);
			_PGC.$$("mtshow", "第" + mcount_max + "次");
		}
	});
});
page_collector.bind_load("attenders", function(){
	let ccount = _PGC.$("cur_meeting_counting");
	_PGC.$$("cmt", {mname: _PGC.$("cur_meeting_name")});
	_PGC.$$("mtshow", "第" + ccount + "次");
	$("#attenders_tbl").data('stable').filter_params.mid = _PGC.$("cur_meeting");
	//$("#attenders_tbl").data('stable').filter_params.mtime = _PGC.$("cur_meeting_counting"); // mtime相当于max，勿修改
	$("#attenders_tbl").data('stable').filter_params.mcount = ccount; // mtime相当于max，勿修改
	
	$("#attenders_tbl").stable("go_page", 1);
});

// PAGE: 学校用户导入和管理
page_collector.bind_ini("schoolusers", function(){
	let pager = this;
	_PGC.$("dlg_withsubs", false);
	// INITAL TABLE
	$("#schoolusers_tbl").stable({
		source_url: '/resource/users?action=list', 
		filter_params: null,
		tbl_bar: '#schoolusers_bar',
		key_name: 'uid',
		last_id: 0,
		page_limit: 50,
		autoload: true,
		pagedata: [],
		filter_zoom: '',
		prtmnt: (r)=>{
			//uid,userid,wxuserid,openid,username,regdtime,status
			if (r.status === 1){
				r.reg_status = "已注册";
			}else if (r.status === 0){
				r.reg_status = "未注册";
			}
			r.dpname = _dpmap[r.departid];
			return r;
		},
		row_tmpl: '<tr rownum="${row.uid}"><td>${row.userid}</td><td>${row.openid}</td><td>${row.dpname}</td><td>${row.username}</td><td>${row.regdtime}</td><td>${row.reg_status}</td><td><button class="btn btn-sm act1" type="button">MSG</button><button class="btn btn-sm act2" type="button">DETIAL</button><button class="btn btn-sm act3" type="button">-</button></td></tr>',
		innerbtn_actions: [
			['信息', 'act1', function(r){
				content = prompt("输入内容");
				if (content){
					let row = $("#schoolusers_tbl").data("stable")['selections'];
					$.post("/api/message?action=send_user", {wxuserid: row.wxuserid, content: content}, function(rsp){
						//console.log(rsp);
					}, 'json');
				}
			}],
		],
	});
	// ini actions

	let dom_ul = document.getElementById("depart_tree2");
	// bind UI actions
	this.querySelector("#btn_import_all").onclick = function(evt){
		alert("智慧校园暂不支持");
	}
	// 部门导入
	this.querySelector("#btn_import_dpt").onclick = function(){
		// load depart-user data and open-show in dlg
		if (!_departments){
			return;
		}
		if (dom_ul.children.length < 1){
			let dps = FUNCS.data_convert(_departments, {title: 'departname', id: 'departid', child: 'child'});
			$(dom_ul).data('zui.tree').reload(dps);
		}
		_PGC.$("userby", "all");
		dlg_mgm.opendlg("choose_bydpart");
	}
	//dlg_dp.querySelector("[name='include_subs']").onclick = function(e){
	//	console.log(e.target);
	//	_PGC.$("dlg_withsubs", e.target.value === 1);
	//}
});

page_collector.bind_ini("room_schedule", function(){
	_PGC.$("pre_roomid", 0);
	_PGC.settriggers({
		cur_rname: "#rs_cur_rname",
		on_date_s: {target: '[name="schedule_date_s"]', value:new Date().toISOString().substr(0,10)},
		on_date_e: {target: '[name="schedule_date_e"]', value:""},
		cur_room_schedule: {target: 'schedule_listor', mode: 'innertpl', value: '<ul class="list-group">(for datas:<li class="list-group-item">会议名称：${mname} | 召开日期：${ondate} | 时间：${time_begin}-${time_end}；</li>)</ul>'}
	});
	//按照单日查看
	document.getElementById("schedule_single").onclick = function(){
		let c_rid = _PGC.$("sel_roomid", undefined, "mroom");
		if(c_rid === 0){
			alert("未指定会议室");
			return;
		}
		//console.log(_PGC.$$("cur_rname"));
		let ondate = _PGC.$$("on_date_s");
		if (!ondate){
			ondate = new Date().toISOString().substr(0,10);
			_PGC.$$("on_date_s", ondate);
		}
		//console.log(ondate);
		$.getJSON("/resource/mroom", {action: "schedule",roomid:c_rid, period_from: ondate, period_end: _PGC.$$("on_date_e")}, function(rsp){
			if (rsp.success === 'yes'){
				if (rsp.data && rsp.data.length>0){
					_PGC.$$("cur_room_schedule", {datas: rsp.data});
					_PGC.$("pre_roomid", c_rid);
				} else{
					document.getElementById("schedule_listor").innerText = "无数据";
				}
				_PGC.$("pre_roomid", c_rid);
			}
		});
	}
});
page_collector.bind_load("room_schedule", function(){
	_PGC.$$("cur_rname", _PGC.$("sel_roomn", undefined, "mroom"));
	_PGC.$$("on_date_s", new Date().toISOString().substr(0,10));
	document.getElementById("schedule_single").click();
});
// 会议新增页面
page_collector.bind_ini("meeting_create", function(){
	_PGC.$({
		work_mode: 'new',
		mroom: 0,
		rpmode: 0,
		room_identifier: "",
		sign_mode: 0
	});
	_PGC.settriggers({
		mc_title: "#mc_title",
		ipt_name: '[name="name"]',
		ipt_ondate: '[name="ondate"]',
		ipt_ontime: '[name="ontime"]',
		ipt_pstart: '[name="p_start"]',
		ipt_pend: '[name="p_end"]',
		ipt_mtime: {target: '[name="mtime"]', value: 120},
		dis_roomn: {target: '#mc_chooseroom', mode: "text", value: "未指定会议室"},
	});
	// UI ACTIONS
	let page = document.getElementById("meeting_create");
	page.querySelector('[name="rpmode"]').onchange = function(evt){
		let show=0,hide=2;
		if (this.value == 0){
			show = 0;
			hide = 2;
		}else {
			show = 2;
			hide = 0;
		}
		page.querySelectorAll(".mode" + show).forEach((n)=>{n.style.display='table'});
		page.querySelectorAll(".mode" + hide).forEach((n)=>{n.style.display='none'});
		_PGC.$("rpmode", this.value);
	}
	// 更多
	page.querySelector("#mc_extend").onclick = function(evt){
		page.querySelectorAll(".mc_ext").forEach((n)=>{n.style.display='table'});
	}
	// open dialog to choose room
	page.querySelector("#mc_chooseroom").onclick = function(evt){
		dlg_mgm.opendlg("mroom_chooser");
	}
	// DLG UI ACTIONS:
	document.getElementById("ms_show_mrooms").onclick = function(evt){
		// 会议室选择器
		let dlg = document.getElementById("dlg_mroom_selector");
		let filterv = dlg.querySelector('[name="chooseby"]:checked').value;
		let sign_mode_v = dlg.querySelector('[name="choose_sign_mode"]:checked').value;
		let params = {
			filterv,
			action: 'available',
			sign_mode: sign_mode_v,
		}
		//console.log(params);
		if (filterv == 0){
			_PGC.$("selected_mroom", 0);
			return;
		} else if (filterv == 1){
			//pass
		} else if (filterv == 2){
			console.log(_PGC.$("rpmode"));
			if (_PGC.$("rpmode") > 0){
				alert("只有一次性会议才能根据日期筛选会议室");
				return;
			}
			params.ondate = _PGC.$$("ipt_ondate");
			params.ontime = _PGC.$$("ipt_ontime");
			params.mtime = _PGC.$$("ipt_mtime") || 120;
			if(!params.ondate){
				alert("请至少指定一个日期");
				return;
			}
		}
		//console.log(params);
		$.getJSON(_exec.make_urlparam(params, '/resource/mroom'), function(rsp){
			let dlg = document.getElementById("dlg_mroom_selector");
			let selr = dlg.querySelector('[name="ms_mroom_list"]');
			if(rsp && rsp.success === 'yes'){
				//roomid,objid,name,room_identifier,sign_mode,allow_people,next_meeting,next_mdtime,status
				_exec.set_sel_opts_ex(selr, rsp.data, null, 'name', 'roomid', ['room_identifier','sign_mode','allow_people']);
			}else{
				_exec.set_sel_opts_ex(selr);
				emsger.show("无数据");
			}
		});
	}
	// OK 提交新增/修改
	page.querySelector("#mc_ok").onclick = function(evt){
		// check data's legality
		let page = document.getElementById("meeting_create");
		let sign_pre = page.querySelector('[name="sign_pre"]').value, sign_limit = page.querySelector('[name="sign_limit"]').value;
		params = {
			name: _PGC.$$("ipt_name"),
			mroom: _PGC.$("mroom"),
			roomname: _PGC.$$("dis_roomn"),
			sign_mode: _PGC.$("sign_mode"),
			rpmode: _PGC.$("rpmode"),
			ondate: _PGC.$$("ipt_ondate"),
			ontime: _PGC.$$("ipt_ontime") + ":00",
			mtime: _PGC.$$("ipt_mtime") || 120,
			room_identifier: _PGC.$("room_identifier"),
		};
		if(sign_pre){
			params['sign_pre'] = sign_pre;
		}
		if (sign_limit){
			params['sign_limit'] = sign_limit;
		}
		if(params.rpmode > 0){
			params['rparg'] = page.querySelector('[name="rparg"]').value;
			params['p_start'] = _PGC.$$("ipt_pstart");
			params['p_end'] = _PGC.$$("ipt_pend");
		};
		console.log(params);
		_PGC.$("cur_meetingdata", params);
		if (_PGC.$("work_mode") === 'modify'){
			if (params.rpmode > 0){
				alert("周期性会议暂不支持修改，请另外新建");
				return;
			}
			delete params.name;
			delete params.rpmode;
		}
		$.post('/api/meeting?action=' + _PGC.$("work_mode"), params, function(rsp){
			if(rsp && rsp.success === 'yes'){
				if(!rsp.data || rsp.data.mid < 0){
					emsger.show("提交成功，但是服务器错误，操作失败!");
					return;
				}
				imsger.show("OK");
				_PGC.$("cur_meetingdata")['mid'] = rsp.data.mid;
				_PGC.$("cur_meetingdata")['nextdtime'] = rsp.data.nextdtime;
				_PGC.$("addnew", 'success', "meeting");
				_PGC.go_page(_PGC.main_pg);
			}else {
				emsger.show("操作失败!" + rsp.msg);
				_PGC.$("cur_meetingdata", null);
				//_PGC.go_page(_PGC.main_pg);
			}
		}, 'json');
	}
	page.querySelector("#mc_cancel").onclick = function(evt){
		go_page('meeting');
	}
});
page_collector.bind_load("meeting_create", function(){
	if(_PGC.$("work_mode") === 'modify'){
		_PGC.$$("mc_title", "会议修改");
		// set value to data
		if (!_PGC.$("cur_meeting")){
			alert("未指定会议");
			_PGC.go_page(_PGC.main_pg);
		}
		let meetingdata = _PGC.$("cur_meetingdata");
		let $page_as_dlg = $("#meeting_create");
		dlg_mgm.set_values($page_as_dlg, meetingdata);
		_PGC.$$("dis_roomn", meetingdata.roomname);
		// handle when rpmode > 0
		$page_as_dlg.find('[name="name"]')[0].disabled = true;
		$page_as_dlg.find('[name="rpmode"]')[0].disabled = true;
	}else if (_PGC.$("work_mode") === 'new'){
		_PGC.$("new_mdata", null);
		_PGC.$$("mc_title", "会议建立");
		_PGC.$("cur_meetingdata", null);
		dlg_mgm.set_values($("#meeting_create"), {}, true);
		// set selection
		let seler = document.querySelector("#meeting_cdata select");
		seler.selectedIndex = 0;
		let e = new CustomEvent("change");
		seler.dispatchEvent(e);
		document.getElementById("meeting_create").querySelectorAll("[name]").forEach((d)=>{
			d.disabled=false;
		});
	}
});

// PART OF DIALOGS
dlg_mgm.inital({
	'attender': {
		name: 'attender',
		did: '#dlg_attender',
		validate: false,
		smb: '.go_submit',
		on_submit: function(dlg){
			let selr = document.querySelector(dlg.did).querySelector("#all_in_dpart");
			//console.log(selr.value);
		},
	},
	'mroom': {
		name: 'mroom',
		did: '#dlg_mroom',
		fid: '#frm_mroom',
		validate: false,
		on_response: function(rsp){
			if(rsp && rsp.success === 'yes'){
				if (_PGC.$("m_dlg_mode") === 'new'){
					imsger.show("建立成功！");
					if (!rsp.data || rsp.data <= 0){
						return;
					}
					let rowdata = dlg_mgm.last_data[this.name];
					rowdata['roomid'] = rsp.data || 0;
					rowdata['next_meeting'] = '-';
					rowdata['next_mdtime'] = '-';
					$("#mroom_tbl").stable('insert_row', 1, rowdata);
				} else if (_PGC.$("m_dlg_mode") === 'modify'){
					imsger.show("修改成功！");
					let rowdata = dlg_mgm.last_data[this.name];
					//console.log(JSON.stringify(rowdata));
					$("#mroom_tbl").stable('set_row_byid', rowdata['roomid'], rowdata);
				}
				dlg_mgm.closedlg(this.name);
			}else{
				emsger.show("失败!");
			}
		},
		smb: '.go_submit',
		on_submit: function(dlg){
			let $dlg = this._$dlg();
			let params = this.get_json($dlg);
			let act = _PGC.$("m_dlg_mode");
			if (act === 'modify'){
				params['roomid'] = _PGC.$("m_dlg_roomid");
			}
			if (params['sign_mode'] == 0){
				params['room_identifier'] = "";
			}
			this.post_form($dlg, "/api/mroom?action=" + _PGC.$("m_dlg_mode"), params);
		},
		on_changes: {
			'sign_mode': function(n,v){
				let $dlg = this._$dlg();
				if (v == 0){
					$dlg.find('[name="room_identifier"]').prop("disabled", true);
				} else {
					$dlg.find('[name="room_identifier"]').prop("disabled", false);
				}
			},
		},
	},
	'mroom_chooser': {
		name: 'mroom_chooser',
		did: '#dlg_mroom_selector',
		fid: '#frm_mroom_selector',
		smb: '.go_submit',
		on_submit: function(dlg){
			// put select-value[s] to page-dialog:[mroom/roomname/room_identifier
			let $dlg = this._$dlg();
			let seler = $dlg.find('[name="ms_mroom_list"]')[0];
			if($dlg[0].querySelector('[name="chooseby"]:checked').value == 0){
				_PGC.$("mroom", 0);
				_PGC.$$("dis_roomn", "不指定会议室");
				_PGC.$("room_identifier", "");
			} else {
				let opt = seler.options[seler.selectedIndex];
				_PGC.$("mroom", opt.value);
				_PGC.$$("dis_roomn", opt.textContent);
				_PGC.$("room_identifier", opt.dataset.room_identifier);
				if(opt.dataset.room_identifier){
					_PGC.$("sign_mode", 1);
				}
			}
			$dlg.modal('toggle');
		},
	},
	'choose_bydpart': {
		// common usage
		name: 'choose_bydpart',
		did: '#dlg_departments',
		smb: '.go_submit',
		on_response: function(rsp){
			let for_win=_PGC.cur_page;
			//console.log(rsp);
			if(rsp && rsp.success==='yes'){
				dlg_mgm.closedlg();
				if (for_win === 'schoolusers'){
					$("#schoolusers_tbl").stable("go_page", 1, true, null, true);
				} else if (for_win === 'attenders'){
					$("#attenders_tbl").stable("go_page", 1, false, {mid: _PGC.$("cur_meeting")}, true);
				}
			} else if (rsp.msg !== 'done') {
				emsger.show("失败：" + rsp.msg);
			} else {
				emsger.show("失败的操作");
			}
			//reflash table when success
		},
		on_submit: function(dlg){
			let for_win=_PGC.cur_page, url, params;
			let $dlg = this._$dlg();
			let seler = $dlg.find('#users_in_dpart')[0];
			let opts = seler.options;
			let seled_opts = [];
			for(let o,i=0,len=opts.length;i<len;i++){
				o = opts[i];
				if(!o.selected){continue}
				if(for_win === 'attenders'){
					seled_opts.push({
						userid: o.value,
						wxuserid: o.dataset.wxuserid,
						username: o.textContent,
						roleid: 0,
					});
				}else if (for_win === 'schoolusers'){
					seled_opts.push({userid: o.value, wxuserid: o.dataset.wxuserid, username: o.textContent, departid: o.dataset.departid, cellphone: o.dataset.cellphone});
				}
			}
			//console.log(seled_opts);
			if (for_win === 'attenders'){
				url = '/api/attenders?action=add';
				params = {
					mid: _PGC.$("cur_meeting"),
					attenders: seled_opts,
					mcount: $("#attenders_tbl").data('stable').filter_params.mcount
				};
			} else if (for_win === 'schoolusers'){
				url = '/api/users?action=import';
				params = {users: seled_opts};
			} else {return;}
			this.post_form($dlg, url, params);
			//$.post("/api/users?action=import", {users: seled_opts}, function(rsp){
			//	console.log(rsp);
			//}, 'json');
		},
	},
});

$(document).ready(function(){
	$(".form-time").datetimepicker({
		language:  "zh-CN",
		weekStart: 1,
		todayBtn:  1,
		autoclose: 1,
		todayHighlight: 1,
		startView: 1,
		minView: 0,
		maxView: 1,
		forceParse: 0,
		format: 'hh:ii'
	}).on('changeDate', function(ev){_PGC.$$("ipt_ontime", ev.date.toISOString().substr(11,5))});
	
	$.getJSON("/school?action=schoolinfo", function(rsp){
		if(rsp && rsp.success === 'yes'){
			document.getElementById("logoimg").src = "https://p.qpic.cn/smartcampus/0/" + rsp.data.logo + "/0";
			document.getElementById("logotext").textContent = rsp.data.name;
		}
	});
});