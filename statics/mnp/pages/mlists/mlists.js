// pages/mlists/mlists.js
const app = getApp();
Page({

  /**
   * 页面的初始数据
   */
  data: {
    meetings: null,
  },
  _set_off: function(mid){
    this.data.meetings.forEach((m,i)=>{
      if (m.mid === mid){
        let s = 'meetings[' + i + '].off';
        this.setData({
          [s]: true,
        })
      }
    });

  },
  ask_off: function(e){
    let mid = Number(e.target.dataset.mid);
    let userid = app.globalData.userid;
    let _this = this;
    console.log(mid);
    wx.showModal({
      title: "提示",
      content: "请假不能取消，是否确定请假？",
      success(res){
        if (res.confirm) {
          wx.request({
            url: 'https://attend.hitouch.cn/api/meeting?action=ask_off&userid=' + userid,
            method: 'POST',
            data: {userid: userid, mid: mid},
            header: {
              'content-type': 'application/x-www-form-urlencoded'
            },
            success(res){
              let rsp = res.data;
              console.log(rsp);
              if (rsp && rsp.success === 'yes'){
                wx.showToast({
                  title: '请假成功！',
                });
                _this._set_off(mid);
              } else {
                wx.showModal({
                  title: "失败",
                  cancelColor: 'cancelColor',
                })
              }
            },
          });
        }else if (res.cancel) {
          return;
        }
      },
    });

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
    app.globalData.meetings.forEach((m)=>{
      if (m.status === 3){
        m.off = true;
      }else{
        m.off = false;
      }
    })
    this.setData({ meetings: getApp().globalData.meetings });
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