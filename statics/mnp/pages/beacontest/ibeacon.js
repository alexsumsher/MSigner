// pages/beacontest/ibeacon.js
Page({

  /**
   * 页面的初始数据
   */
  data: {
    working: true,
  },
  // EVENTS
  doTest: function(){

    this.setData({working: true});
    var that = this;

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
          wx.startBeaconDiscovery({//开始搜索附近的iBeacon设备
            uuids: ['AB8190D5-D11E-4941-ACC4-42F30510B408'],//参数uuid
            success: function (res) {
              if (that.data.working === false){
                return;
              }
              wx.onBeaconUpdate(function (res) {//监听 iBeacon 设备的更新事件  
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
  },
  endTest: function(){
    this.setData({working: false});
    wx.stopBeaconDiscovery({
      success: res=>{
        wx.showToast({
          title: 'STOP beacon done!',
        })
      },
      fail: res=>{
        wx.showToast({
          title: 'STOP beacon Failure!',
        })
      }
    })
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad: function (options) {

  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady: function () {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow: function () {

  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide: function () {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload: function () {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh: function () {

  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom: function () {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage: function () {

  }
})