const formatTime = date => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return [year, month, day].map(formatNumber).join('/') + ' ' + [hour, minute, second].map(formatNumber).join(':')
}

const formatNumber = n => {
  n = n.toString()
  return n[1] ? n : '0' + n
}

const meeting_generator = function(date, time, place){
  var places = ['大会议室', '小会议室', '礼堂', '活动室', '408'];
  var titles = ['安全工作会议', '工作会议', '周会', '例会', '教学组会议', '年级会议'];
  let aday = 24 * 60 * 60 * 1000;
  if (!date) {
    let nowtime = new Date().getTime();
    let offset_days = Math.round(Math.random() * 7);
    let offset_date = nowtime + offset_days * aday;
    date = new Date(offset_date);
  } else if (date <= 7) {
    // offset of day
    let offset_date = nowtime + date * aday;
    date = new Date(offset_date);
  } else if (typeof (date) === 'string') {
    newdate = new Date(date);
  }
  // limit offset of 7day
  if (!time) {
    let _rnd = Math.random();
    time = 8 + Math.round(_rnd) * 10 + (_rnd > 0.5 ? ':30' : ':00');
  }
  let ln = places.length - 1;
  if (!place) {
    place = places[Math.round(Math.random() * ln)];
  }
  ln = titles.length - 1;
  let title = titles[Math.round(Math.random() * ln)];
  return {
    title: title,
    mtid: Math.round(Math.random() * 100),
    date: date.toLocaleDateString(),
    time: time,
    place: place
  }
}

module.exports = {
  formatTime: formatTime,
  meeting_gen: meeting_generator,
}
