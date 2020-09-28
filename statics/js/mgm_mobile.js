//mgm_mobile
var Cells = {
  template: '#cells',
  data() {
	//var cukyRE = new RegExp('\;{0,1}username=(.*?);');
	var cukyRE = /\;{0,1}\s+username=(\w+?)(\;|$)/;
	var uname;
	try{
		uname = cukyRE.exec(document.cookie)[1];
	}catch(e){
		uname = "";
	}
	return {
		topmsg: "欢迎，" + uname + "老师",
	  entrances: [
		'<div class="entrance assertive"><img class="icon" src="../imgs/meetingroom2.png"></img><br><span>会议室</span></div>',
		'<div class="entrance energized"><img class="icon" src="../imgs/meetingmgm.png"></img><br><span>会议</span></div>',
		'<div class="entrance balanced"><img class="icon" src="../imgs/meetingpeaple.png"></img><br><span>人员</span></div>',
		'<div class="entrance positive"><img class="icon" src="../imgs/new_meeting1.png"></img><br><span>+一次会议</span></div>',
		'<div class="entrance positive"><img class="icon" src="../imgs/new_meeting2.png"></img><br><span>+周期会议</span></div>',
	  ]
	}
  },

  methods: {
	onCellClick(cellIndex) {
	  console.log('cell ' + cellIndex + ' clicked');
	  
	  if (cellIndex === 3){
		$router.push('new_meeting1');
	  }if (cellIndex === 4){
		$router.push('new_meeting2');
	  }else if (cellIndex === 1){
		$router.push('meetinglist');
	  }else if (cellIndex === 0){
		$router.push('mroomlist');
	  }else if (cellIndex === 2){
		  if (_gbl_env.cur_meeting){
			  _gbl_env.cur_meeting.mid = 0;
		  }
		  $router.push('userlist');
	  }
	},
  }
};

var Pg_listmeetings = {
	template: '#mlists',
	data(){
		axios.get("/resource/meeting?action=mlist&overtime=no&page=1&page_limit=100").
		then((response)=>{
			let rd = response.data.data;
			rd.forEach((n)=>{
				if (n.rpmode === 1){
					n.rpmode_txt = "周期会议(周)";
				}else if(n.rpmode === 2){
					n.rpmode_txt = "周期会议(月)";
				} else {
					n.rpmode_txt = "一次性会议";
				}
			});
			this.all_meetings = rd;
		});
		return {
			all_meetings: [
				{mid: 1, name: '......'},
			],
		};
	},
	methods: {
		setattender(i){
			let target = this.all_meetings[i];
			let show = target.name;
			$toast.show(show);
			if(target.rpmode === 0 && (new Date(target.nextdtime) < new Date())){
				alert("会议已经过期");
				return;
			}
			_gbl_env.cur_meeting = {
				mid: target.mid,
				name: target.name,
			}
			$router.push('userlist');
		},
		getattenders(i){
			let target = this.all_meetings[i];
			_gbl_env.cur_meeting = {
				mid: target.mid,
				name: target.name,
				counting: target.couting,
			}
			console.log(JSON.stringify(_gbl_env));
			this.$router.push('attenderlist');
		},
		meetinginfo(i){
			// 会议信息
			let m = this.all_meetings[i];
			let showhtml = "<span>名称：</span>" + m.name + "<br><span>会议室：</span>" + m.roomname + "<br><span>会议时间：</span>"
			+ m.nextdtime + "<br><span>是否签到：" + (m.sign_mode===0?"不需要":"需要");
			$dialog.alert({
				title: m.name,
			  content: "",
			  okTheme: 'positive',
			  effect: 'default'
			}).then(() => {
			})
			document.querySelector(".popup-body").innerHTML = showhtml;
		},
	}
};

var Pg_meeting1 = {
	template: '#new_meeting1',
	data(){
		return {
			m_name: '',
			m_ondate: new Date().toISOString().substr(0,10),
			m_ontime: "8:00",
			m_cost: "120",
			m_roomid: 0,
			m_roomname: "不指定会议室",
			m_signmode: 0,
			m_signpre: 10,
			m_signlimit: 30,
		}
	},
	methods: {
		submeeting1(){
			if (!_input_checker("m_ontime", this.m_ontime)){
				console.log("check failure");
				return;
			}
			let _ontime = this.m_ontime + ":00";
			if (_ontime.length < 8){
				_ontime = "0" + _ontime;
			}
			let postdata = {
				name: this.m_name,
				rpmode: 0,
				sign_mode: this.m_signmode,
				ondate: this.m_ondate,
				ontime: _ontime,
				mtime: this.m_cost,
				mroom: this.m_roomid,
				roomname: this.m_roomname,
				sign_pre: this.m_signpre,
				sign_limit: this.m_signlimit,
			};
			//alert(JSON.stringify(postdata));
			d_cmds.create_meeting(postdata, (data)=>{
				$toast.show("提交成功!", 1000);
				this.$router.go(-1);
			});
			//$toast.show("提交成功！", 1000).then(() => {
			//  $router.go(-1);
			//});
		},
		for_room(){
			_page_helper.room_seler(this, {
				action: 'available',
				filterv: 1,
				sign_mode: 0,
				ondate: this.m_ondate,
				ontime: this.m_ontime,
				mtime: this.mtime
			});
		},
	}
};

var Pg_meeting2 = {
	template: '#new_meeting2',
	data(){
		return {
			m_signmode: 0,
			m_name: '',
			m_type: 1,
			m_typename: '按周重复',
			m_ondate: '',
			m_ontime: "8:00",
			m_cost: "120",
			p_start: new Date().toISOString().substr(0,10),
			p_end: "",
			m_roomid: 0,
			m_roomname: "不指定会议室",
			info: "用‘，’隔开；月周期循环请留意每个月长度不一致，用-1表示最后一天",
		}
	},
	methods: {
		submeeting2(){
			if (!_input_checker("m_ontime", this.m_ontime)){
				return;
			}
			let _ontime = this.m_ontime + ":00";
			if (_ontime.length < 8){
				_ontime = "0" + _ontime;
			}
			let postdata = {
				name: this.m_name,
				rpmode: this.m_type,
				sign_mode: this.m_signmode,
				rparg: this.m_ondate,
				ontime: _ontime,
				mtime: this.m_cost,
				mroom: this.m_roomid,
				p_start: this.p_start,
				p_end: this.p_end
			};
			//alert(JSON.stringify(postdata));
			d_cmds.create_meeting(postdata, (data)=>{
				$toast.show("提交成功!", 1000);
			});
			//$toast.show("提交成功！", 1000).then(() => {
			//  $router.go(-1);
			//});
		},
		for_room(){
			_page_helper.room_seler(this, {
				action: 'available',
				sign_mode: 0,
				filterv: 0,
			});
		},
		for_mtype(){
			_page_helper.mtype_seler(this);
		},
	}
};

var Pg_userlist = {
	template: '#userlist',
	data(){
		return{
			users: [],
			page: 1
		}
	},
	mounted(){
		axios.request({url: "/resource/users", method:'get', params: {action: 'list', page: 1, size: 100}}).then((rsp)=>{
			rsp.data.data.forEach((u)=>{
				u.selsta = "-";
				u.dpname = _dpmap[u.departid];
				this.users.push(u);
			});
			this.top = 1;
			this.bottom = 20;
			_gbl_env.seled_users = [];
		});
	},
	methods: {
		onInfinite(done) {
			if (this.page === -1){console.log("pagelover-1");done();return;}
			$toast.show("onInfinite", 500);
			this.page++;
			axios.request({url: "/resource/users", method:'get', params: {action: 'list', page: this.page, size: 100}}).then((rsp)=>{
				if (!rsp.data.data || rsp.data.data.length === 0){
					console.log("pagelover");
					this.page = -1;
					done();
					return;
				}
				rsp.data.data.forEach((u)=>{
					u.selsta = "-";
					u.dpname = _dpmap[u.departid];
					this.users.push(u);
				});
				//this.users.push(...rsp.data.data);
				//this.top = this.bottom + 1;
				this.bottom += rsp.data.data.length;
				console.log("page:" + this.page + "\t" + this.top + "::" + this.bottom);
				done();
			});
		},
		userok(){
			if (!_gbl_env.cur_meeting || _gbl_env.cur_meeting.mid === 0){
				// 无目标会议
				this.$router.go(-1);
				return;
			}
			this.users.forEach((u)=>{
				if (u.selsta === '已选'){
					_gbl_env.seled_users.push({
						userid: u.userid,
						wxuserid: u.wxuserid,
						username: u.username,
						roleid: 0
					});
				}
			});
			console.log(_gbl_env.seled_users);
			if (_gbl_env.seled_users.length === 0){
				this.$router.go(-1);
				$toast.show("未选择教师", 500);
				return;
			}
			d_cmds.set_attenders({
				mid: _gbl_env.cur_meeting.mid,
				attenders: _gbl_env.seled_users
			}, (res)=>{
				$toast.show("成功添加教师", 500);
				_gbl_env.seled_users.length = 0;
				this.$router.go(-1);
			});
		},
		adduser(idx){
			let u = this.users[idx];
			if (u.selsta === '-'){
				u.selsta = '已选';
				u.cls="icon_active";
			} else {
				u.selsta = '-';
				u.cls="icon_blur";
			}
		},
		testuser(idx){},
	}
};

var Pg_meetinguser = {
	template: '#meetingusers',
	data(){
		return {
			mname: _gbl_env.cur_meeting.name,
			attenders: [],
		}
	},
	mounted(){
		console.log(JSON.stringify(_gbl_env));
		axios.request({url: "/resource/attenders", method:'get', params: {
			mid: _gbl_env.cur_meeting.mid,
			mtime:_gbl_env.cur_meeting.counting,
			action: 'list',
			page: 1,
			size: 100}})
			.then((rsp)=>{
				if (rsp.data.success!=='yes'){return}
				rsp.data.data.forEach((u)=>{
					u.cls = "icon_blur";
					//u.dpname = _dpmap[u.departid];
					this.attenders.push(u);
				});
			});
	},
	methods: {
		detailuser(idx){
			console.log(_gbl_env);
		},
	}
};

var Pg_mrooms = {
	template: '#mgm_mrooms',
	data(){
		axios.get("/resource/mroom?action=list&page=1").
		then((response)=>{
			let rd = response.data.data;
			this.all_mrooms = rd;
		});
		return {
			all_mrooms: [
				{roomid: 1, name: '......'},
			],
		};
	},
	methods: {
		mroominfo(i){
			let m = this.all_mrooms[i];
			let showhtml = "<span>名称：</span>" + m.name + "<br><span>人数上限：</span>" + (m.allow_people || "不限") + "<br><span>签到编码：</span><br>" + (m.room_identifier || "无<br>");
			console.log(showhtml);
			$dialog.alert({
				title: m.name,
			  content: "",
			  okTheme: 'positive',
			  effect: 'default'
			}).then(() => {
			})
			document.querySelector(".popup-body").innerHTML = showhtml;
		},
	}
};

var routes = [
	{path: '/', component: Cells},
	{path: '/new_meeting1', component: Pg_meeting1},
	{path: '/new_meeting2', component: Pg_meeting2},
	{path: '/meetinglist', component: Pg_listmeetings},
	{path: '/mroomlist', component: Pg_mrooms},
	{path: '/userlist', component: Pg_userlist},
	{path: '/attenderlist', component: Pg_meetinguser},
];

Vue.use(Vonic.app, {
	routes: routes
})