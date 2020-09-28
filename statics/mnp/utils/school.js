const check_user = function(tempCode, after){
  // check if user on server
  let userid = wx.getStorageSync("userid");
  if (userid){
    return userid;
  }
  wx.request({
    url: 'http://127.0.0.1:7890/regs?js_code=' + tempCode,
    success: res => {
      rsp = res.data;
      if (rsp.success == 'yes'){
        if (typeof(after) === 'function'){
          after(rsp);
        }
        wx.showToast({
          title: 'msg: check_user ok!',
          mask: true,
          success: function(res) {},
          fail: function(res) {},
          complete: function(res) {},
        });
        wx.setStorage({
          key: 'userid',
          data: rsp.userid
        });
      }
    },
  })
};

const do_beacon = function (times, devices, onsuccess) {
  if (times === 0){
    times = 999;
  } else if (times === -1){
    wx.offBeaconUpdate(()=>{"STOP beacon update!"});
    wx.stopBeaconDiscovery({
      success: ()=>{console.log("STOP beacon descovery!")},
    });
    return;
  }

  if (!devices){
    devices = ['ab8190d5-d11e-4941-acc4-42f30510b408'];
  } else if (!(devices instanceof Array)){
    devices = [devices];
  }

  //监测蓝牙状态的改变
  wx.onBluetoothAdapterStateChange(function (res) {
    if (res.available) {//如果用户打开蓝牙，开始搜索IBeacon
      searchBeacon();
    }
  })

  //搜索beacons
  searchBeacon();
  //搜索函数
  function searchBeacon() {
    //检测蓝牙状态
    let counter = 0;
    wx.openBluetoothAdapter({
      success: function (res) {//蓝牙状态：打开
        console.log("ibeacon for " + times + " times!");
        wx.startBeaconDiscovery({//开始搜索附近的iBeacon设备
          uuids: devices,//参数uuid
          success: function (res) {
            wx.onBeaconUpdate(function (res) {//监听 iBeacon 设备的更新事件  
              console.log(counter);
              //封装请求数据 
              var beacons = res.beacons;
              var reqContent = {};
              var bleArray = [];
              for (var i = 0; i < beacons.length; i++) {
                var bleObj = {};
                bleObj.distance = beacons[i].accuracy;
                bleObj.rssi = beacons[i].rssi;
                bleObj.mac = beacons[i].major + ":" + beacons[i].minor;
                bleArray.push(bleObj);
              }
              reqContent.ble = bleArray;
              console.log(reqContent);
              if (counter++ >= times) {
                wx.offBeaconUpdate(() => { "off beacon update!" });
                if (typeof (onsuccess) === 'function') {
                  onsuccess(reqContent);
                }
                return;
              }
            });
          },
          fail: function (res) {
            //先关闭搜索再重新开启搜索,这一步操作是防止重复wx.startBeaconDiscovery导致失败
            stopSearchBeacom();
          }
        })
      },
      fail: function (res) {//蓝牙状态：关闭
        wx.showToast({ title: "请打开蓝牙", icon: "none", duration: 2000 })
      }
    })
  }
  //关闭成功后开启搜索
  function stopSearchBeacom() {
    wx.stopBeaconDiscovery({
      success: function () {
        searchBeacon();
      }
    })
  }
};

const do_beacon2 = function (times, device, onsuccess){
  if (!times || times === 0) {
    times = 999;
  } else if (times === -1) {
    wx.offBeaconUpdate(() => { "STOP beacon update!" });
    wx.stopBeaconDiscovery({
      success: () => { console.log("STOP beacon descovery!") },
    });
    return;
  }
  if (!device) {
    var devices = ['ab8190d5-d11e-4941-acc4-42f30510b408'];
  } else {
    var devices = [device.toLowerCase()];
  }
  //监测蓝牙状态的改变
  wx.onBluetoothAdapterStateChange(function (res) {
    if (res.available) {//如果用户打开蓝牙，开始搜索IBeacon
      searchBeacon();
    }
  })

  //搜索beacons
  searchBeacon();
  //搜索函数
  function searchBeacon() {
    //检测蓝牙状态
    let counter = 0;
    wx.openBluetoothAdapter({
      success: function (res) {//蓝牙状态：打开
        console.log("ibeacon for " + times + " times!");
        wx.startBeaconDiscovery({//开始搜索附近的iBeacon设备
          uuids: devices,//参数uuid
          success: function (res) {
            let target = devices[0];
            let found = false;
            console.log("find " + target + " in " + times + " times!");
            wx.onBeaconUpdate(function (res) {//监听 iBeacon 设备的更新事件  
              console.log(counter);
              //一直搜索到times为止，如果搜索到beacon则提前结束
              var beacons = res.beacons;
              for (var i = 0; i < beacons.length; i++) {
                if (beacons[i].uuid.toLowerCase() === target){
                  found = true;
                  break;
                }
              }
              console.log(beacons);
              if (found || counter++ >= times) {
                wx.offBeaconUpdate(() => { "off beacon update!" });
                if (typeof (onsuccess) === 'function') {
                  onsuccess(found);
                }
                return;
              } else {
                wx.showModal({
                  title: '提示',
                  content: '搜索不到签到装置：装置是否打开或者没有电？',
                  cancelColor: 'cancelColor',
                })
              }
            });
          },
          fail: function (res) {
            //先关闭搜索再重新开启搜索,这一步操作是防止重复wx.startBeaconDiscovery导致失败
            stopSearchBeacom();
          }
        })
      },
      fail: function (res) {//蓝牙状态：关闭
        wx.showToast({ title: "请打开蓝牙", icon: "none", duration: 2000 })
      }
    })
  }
  //关闭成功后开启搜索
  function stopSearchBeacom() {
    wx.stopBeaconDiscovery({
      success: function () {
        searchBeacon();
      }
    })
  }
};

const do_beacon3 = function (device){
  if (!device) {
    devices = 'AB8190D5-D11E-4941-ACC4-42F30510B408';
  }

  //监测蓝牙状态的改变
  wx.onBluetoothAdapterStateChange(function (res) {
    if (res.available) {//如果用户打开蓝牙，开始搜索IBeacon
      searchBeacon();
    }
  })

  //搜索beacons
  searchBeacon();
  //搜索函数
  function searchBeacon() {
    //检测蓝牙状态
    wx.openBluetoothAdapter({
      success: function (res) {//蓝牙状态：打开
        console.log("ibeacon for " + times + " times!");
        wx.startBeaconDiscovery({//开始搜索附近的iBeacon设备
          uuids: devices,//参数uuid
          success: function (res) {
            wx.getBeacons({
              success: (res)=>{
                console.log(res);
                for (let i=0,len=res.beacons.length;i<len;i++){
                  if (res.beacons[i].uuid === device){
                    console.log("OK with target device: " + device);
                  }
                }
              },
            })
          },
          fail: function (res) {
            //先关闭搜索再重新开启搜索,这一步操作是防止重复wx.startBeaconDiscovery导致失败
            stopSearchBeacom();
          }
        })
      },
      fail: function (res) {//蓝牙状态：关闭
        wx.showToast({ title: "请打开蓝牙", icon: "none", duration: 2000 })
      }
    })
  }
  //关闭成功后开启搜索
  function stopSearchBeacom() {
    wx.stopBeaconDiscovery({
      success: function () {
        searchBeacon();
      }
    })
  }
}

const _meeting_generator = function(date, time, place){
  const places = ['大会议室', '小会议室', '礼堂', '活动室', '408'];
  let aday = 24 * 60 * 60 * 1000;
  if (!date){
    let nowtime = new Date().getTime();
    let offset_days = Math.round(Math.random() * 7);
    let offset_date = nowtime + offset_days * aday;
    date = new Date(offset_date);
  } else if (date <= 7){
    // offset of day
    let offset_date = nowtime + date * aday;
    date = new Date(offset_date);
  } else if (typeof(date) === 'string') {
    newdate = new Date(date);
  }
  // limit offset of 7day
  if (!time){
    let _rnd = Math.random();
    time = 8 + Math.round(_rnd) * 10 + (_rnd>0.5?':30':':00');
  }
  if (!place){
    let ln = places.length - 1;
    place = places[Math.round(Math.random() * ln)];
  }
  return {
    name: '会议名',
    mid: Math.round(Math.random() * 100),
    nextdtime: date.toLocaleDateString(),
    roomname: place
  }
}

module.exports = {
  check_user: check_user,
  do_beacon: do_beacon,
  do_beacon2: do_beacon2
}