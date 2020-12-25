//app.js
App({
  onLaunch: function () {
    wx.clearStorage({
      success: (res) => {console.log("storage is clear!")},
    })
    return;
  },
  globalData: {
    userInfo: null,
    userid: null,
    ukey: null, // 可能是名字或者手机号
    openid: null,
    login_code: null,
    version: 0.91,
    nyobjid: '2XaxJgvRj6Udone',
  }
})