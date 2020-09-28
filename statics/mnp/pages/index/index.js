//index.js
//获取应用实例
const app = getApp();
const signer = require('../../utils/school.js');
Page({
  data: {
    storemode: true,
    is_reg: false,
    userid: '',
    username: '',
    ukey: '', // 用户登陆关键字，系统中登陆的名字或手机号，取消账号
    password: '',
    ustatus: 1, // unreg0, logout1, reged2, login3
    sign_status: "unsigned",
    sign_text: '未签到',
    //sch_array: [],
    sch_id: '2XaxJgvRj6Udone', // objid
    sch_name: '南油小学',
    userInfo: {},
    hasUserInfo: false,
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
    next_meeting: {
      mid: 0,
      nextdtime: '',
      counting: 0,
      name: '当日无后续会议',
      roomname: '',
      identify_key: '',
    }
  },
  // vars
  regcode: null,
  _env: {
    auth: false,
    working: false,
    meettings: [],
    _objid: '2XaxJgvRj6Udone',
    _sch_idx: 0,
    openid: null,
    empty_meeting: { mid: 0, name: "NO", },
  },

  logout: function(){
    // exit->login/reg
    this.setData({ustatus: 1, userid: null});
    this._env.openid = "";
    //this.load_schools();
  },
  login_block: function(){
    this.setData({ustatus: 1});
    return;
    /*
    if (this.data.sch_array.length === 0){
      this.load_schools();
    }
    */
  },
  reg_block: function(){
    this.setData({ustatus: 0});
  },

  //事件处理函数
  bindViewTap: function() {
    wx.navigateTo({
      url: '../logs/logs'
    })
  },
  infostore: function(e){
    let m = !this.data.storemode;
    this.setData({ storemode: m });
  },
  act_keyin: function(e){
    //console.log(e.target.dataset.key + e.detail.value);
    let k = e.target.dataset.key,
        v = e.detail.value;
    this.setData({ [k]: v});
  },
  // 选择学校
  sch_choose: function(e){
    console.log(e);
    let v = parseInt(e.detail.value);
    let n = this.data.sch_array[v].title;
    this._env._objid = this.data.sch_array[v].ikey;
    this._env._sch_idx = parseInt(e.detail.value);
    this.setData({sch_name: n });
  },
  // beacon
  goBeacon: function(){
    wx.navigateTo({
      url: '../beacontest/ibeacon',
    })
  },
  goSign: function(){
    setTimeout(()=>{
      wx.showToast({
        title: '签到成功！',
      });
      this.setData({ sign_status: 'signed', sign_text: '已签到'});
    }, 450);
  },
  goSign2: function(){
    if (this._env.working){
      // turn off
      signer.do_beacon(-1);
      this._env.working = false;
      return;
    }
    this._env.working = true;
    const onok = (data)=>{
      wx.showToast({
        title: data.ble[0].mac,
      });
      this.setData({ sign_status: 'signed', sign_text: '已签到' });
      signer.do_beacon(-1);
    };
    signer.do_beacon(5, null, onok);
  },
  testSign: function(){
    wx.showToast({
      title: '签到!',
    })
  },

  goSign3: function(){
    if (this.data.next_meeting.sign_mode === 0){
      wx.showModal({
        title: '提醒：',
        content: '无需签到',
        cancelColor: 'cancelColor',
      })
      return;
    }
    const onok = (found) => {
      if (found){
        wx.request({
          url: 'https://attend.hitouch.cn/api/meeting?action=sign&userid=' + this.data.userid,
          method: 'POST',
          data: {
            mid: this.data.next_meeting.mid,
            userid: this.data.userid,
            mcount: this.data.next_meeting.counting,
            room_identifier: this.data.next_meeting.room_identifier
          },
          header: {
            'content-type': 'application/x-www-form-urlencoded'
          },
          success: (rsp)=>{
            let rt = rsp.data;
            if (rt && rt.success === 'yes'){
              wx.showToast({
                title: 'OK',
              })
              this.setData({ sign_status: 'signed', sign_text: '已签到' });
            }else{
              wx.showModal({
                title: '提醒：',
                content: rt.msg,
                cancelColor: 'cancelColor',
              })
            }
          },
        })
      }
      
    };
    //onok(true);
    signer.do_beacon2(5, this.data.next_meeting.room_identifier, onok);
  },

  mymeetings: function(){
    wx.navigateTo({
      url: '../mlists/mlists',
    })
  },

  meeteng_reflash: function(e){
    // 会议刷新
    if (!app.globalData.userid){
      wx.showModal({
        content: '无法刷新\n请重新开启小程序',
        cancelColor: 'cancelColor',
      })
      return;
    }
    this.load_meetings();
  },

  load_schools: function(){
    const def_sch_array = [{"idx": 1, "ikey": "2XaxJgvRj6Udone", "title": "南油小学", "value": null, "value_int": 1}, {"idx": 2, "ikey": "noobjid", "title": "测试学校", "value": null, "value_int": 1}];
    wx.request({
      url: 'https://attend.hitouch.cn/wxuser?action=schoolist',
      success: res => {
        let rsp = res.data;
        if (rsp && rsp.success == "yes"){
          this.setData({sch_array: rsp.data});
        } else {
          this.setData({sch_array: def_sch_array});
        }
      },
      fail: res => {
        this.setData({sch_array: def_sch_array});
        //wx.showToast({
        //  title: '失败！获取学校列表。',
        //  icon: 'none'
        //});
      },
    });
  },

  login2: function(){
    // 已注册的情况下登陆
    if(!this._env._objid){
      wx.showModal({
        title: '提醒',
        content: '选择学校',
        cancelColor: 'cancelColor',
      })
      return;
    }
    
    wx.login({
      success: (res)=>{
        let jscode = res.code;
        app.globalData.login_code = jscode;
        wx.request({
          url: 'https://attend.hitouch.cn/wxuser?action=wxlogin',
          data: {
            schoolid: this._env._objid,
            ukey: this.data.ukey,
            password: this.data.password,
            js_code: jscode,
          },
          header: {
            'content-type': 'application/x-www-form-urlencoded'
          },
          method: 'POST',
          success: (res)=>{
            let rsp = res.data;
            if (rsp && rsp.success === 'yes'){
              this.setData({ustatus: 2, userid: rsp.data.userid});
              if (this.data.storemode) {
                let _this = this;
                wx.clearStorage({
                  complete: (res) => {
                    wx.setStorage({
                      key: 'thisuser',
                      data: { ukey: _this.data.ukey, 
                        upwd: _this.data.password, 
                        schoolid:  _this._env._objid,
                        schoolname: _this.data.sch_name,
                      }
                    });
                  },
                });
                app.globalData.userid = rsp.data.userid;
              }
              this.load_meetings(rsp.data.userid);
            } else {
              wx.showToast({
                title: '登陆失败！',
                icon: 'none',
              })
            }
          }
        });
      },
      fail: (r)=>{
        wx.showModal({
          cancelColor: 'cancelColor',
          content: '登陆失败！',
        })
      },
    });
  },

  autologin: function(){
    // 发送 res.code 到后台换取 openId, sessionKey, unionId
    // and than reg
    let page = this;
    wx.showLoading({
      title: '登陆中...',
    });
    wx.request({
      url: 'https://attend.hitouch.cn/wxuser?js_code=' + app.globalData.login_code,
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      success: res => {
        var rsp = res.data;
        if (rsp.success = 'yes') {
          if (rsp.userid) {
            wx.showToast({
              title: '用户已识别，登录成功',
            });
            page._env.userid=rsp.userid;
            page.setData({ is_reg: true, userid: rsp.userid, ustatus: 2});
            wx.setNavigationBarTitle({
              title: "签到：" + rsp.school.title
            })
            // afeter
            this.load_meetings(rsp.userid);
          } else {
            wx.showToast({
              title: '未注册用户，稍后请注册',
              icon: 'none',
            });
            //page.load_schools();
            page.setData({ is_reg: false , ustatus: 0});
          }
          page._env.openid = rsp.openid;
          app.globalData.userid = rsp.userid;
          app.globalData.openid = rsp.openid;
        } else {
          wx.showLoading({
            title: '失败',
            content: '自动登陆失败，请（名称或手机号）\n登陆或注册。'
          })
          //page.load_schools();
          page.setData({ ustatus: 0});
        }
        wx.hideLoading();
      },
      fail: (e) => { wx.hideLoading();}
    })
  },

  doreg: function(){
    // 测试注册
    console.log("go for regist")
    //this.openid = wx.getStorageSync('openid');
    //this.openid = this._env.openid;
    /*
    if(!this._env.openid){
      wx.showModal({
        title: '提醒：',
        content: '注册权限获取失败！无法注册。',
        cancelColor: 'cancelColor',
      })
      return;
    }
    */
    if (!this._env.auth){
      wx.showModal({
        content: '未获得授权',
        cancelColor: 'cancelColor',
      })
      return;
    }
    if(!app.globalData.login_code){
      wx.showModal({
        content: '未获得注册号，可能是授权问题，请关闭再试着登陆',
        cancelColor: 'cancelColor',
      })
      return;
    }
    wx.showLoading({
      title: '注册中，请稍后。。。',
    });
    wx.request({
      url: 'https://attend.hitouch.cn/wxuser?action=regist',
      data: {
        openid: this._env.openid,
        schoolid: this._env._objid,
        userid: this.data.userid,
        ukey: this.data.ukey,
        password: this.data.password,
        js_code: app.globalData.login_code,
      },
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      method: 'POST',
      success: res => {
        let rsp = res.data;
        if (rsp.success == 'yes') {
          wx.showToast({
            title: '成功！请登陆！',
          });
          this.setData({ is_reg: true, ustatus: 1});
          this._env.openid = rsp.data.openid;
        } else {
          wx.showModal({
            cancelColor: 'cancelColor',
            title: '注册失败!',
            content: rsp.msg,
            showCancel: false,
          })
        }
        wx.hideLoading({
          complete: (res) => {},
        })
      },
      fail: res=>{
        wx.showToast({
          title: '注册失败！',
          icon: 'none',
        });
        wx.hideLoading({
          complete: (res) => {},
        })
      },
    })
  },

  onLoad: function () {
    if (app.globalData.userInfo) {
      this.setData({
        userInfo: app.globalData.userInfo,
        hasUserInfo: true
      })
      this.autologin();
    } else if (this.data.canIUse){
      // 由于 getUserInfo 是网络请求，可能会在 Page.onLoad 之后才返回
      // 所以此处加入 callback 以防止这种情况
      app.userInfoReadyCallback = res => {
        this.setData({
          userInfo: res.userInfo,
          hasUserInfo: true
        })
        this.autologin();
      }
    } else {
      // 在没有 open-type=getUserInfo 版本的兼容处理
      wx.getUserInfo({
        success: res => {
          app.globalData.userInfo = res.userInfo
          this.setData({
            userInfo: res.userInfo,
            hasUserInfo: true
          })
          this.autologin();
        }
      })
    }
    
    /* set meetings
    this._env.meettings = [];
    let m1 = this._meeting_generator();
    console.log(m1);
    this.setData({ next_meeting: m1});
    */
  },

  onReady: function(){
    // 授权
    let _this = this;
    wx.getSetting({
      success (res){
        if (!res.authSetting['scope.userInfo']) {
          wx.authorize({
            scope: 'scope.userInfo',
            success (){
              //pass
              _this._env.auth = true;
             // _this.autologin();
            },
            fail(){
              _this._env.auth = false;
            }
          })
        }else{
          _this._env.auth = true;
          //_this.autologin();
        }
      },
    });
    return;
    // 自动登陆，失败则转到手动登陆
    if (this.data.storemode) {
      let _this = this;
      wx.getStorage({
        key: 'thisuser',
        success: function (res) {
          console.log(res);
          _this.setData({
            ukey: res.data.ukey,
            password: res.data.upwd,
            sch_name: res.data.schoolname
          });
          _this._env._objid = res.data.schoolid;
        },
      });
    }
    // load schools
    //console.log("load schools....");
    //this.load_schools();
    //wx.showLoading({
    //  title: '登录系统',
    //})
    //setTimeout(this.login, 500);
    //this.login();
  },

  getUserInfo: function(e) {
    console.log(e)
    app.globalData.userInfo = e.detail.userInfo
    this.setData({
      userInfo: e.detail.userInfo,
      hasUserInfo: true
    })
  },

  load_meetings: function(userid){
    userid = userid || app.globalData.userid;
    wx.request({
      url: 'https://attend.hitouch.cn/resource/meeting?action=mylist&userid=' + userid,
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      success: res => {
        if (res.data.success === 'yes'){
          let meetings = res.data.data;
          console.log(meetings);
          if (!meetings){
            wx.showToast({
              title: '无会议',
              icon: 'none'
            })
          }
          if (meetings && meetings.length > 0){
            // range for next meeting
            app.globalData.meetings = meetings;
            let m1,dt,now=new Date();
            let smin = 24 * 60 * 60 * 1000;
            meetings.forEach((n)=>{
              // 跳过已签到
              if (n.signtime || n.sign_mode === 0){return}
              console.log(n.nextdtime);
              dt = new Date(n.nextdtime) - now + n.sign_limit * 60 * 1000;
              if (dt<0){
                // 加上time limit 还是超时说明不能签到，直接跳过
                n.signable = false;
                return;
              }
              console.log("dt: " + dt);
              if (dt > 0 && dt < smin){
                m1 = n;
                smin = dt;
              }
            });
            if (m1){
              this.setData({ next_meeting: m1, status: m1.status == 1 ? "signed" :"unsigned" });
            } else{
              // 全部签到或过时，选择最后一个
              console.log("no next meeting");
              m1 = meetings[meetings.length-1];
              if (!m1.signable){
                return;
              }
              this.setData({ next_meeting: m1, status: m1.status == 1 ? "signed" :"unsigned" });
            }
          } else {
            meetings = [];
            app.globalData.meetings = meetings;
          }
        }
      },
    })
  },
})
