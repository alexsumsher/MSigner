var imsger = new $.zui.Messager('', {type: 'primary', time: 3000, icon: 'icon-bolt'});
var emsger = new $.zui.Messager('', {type: 'danger', time: 3000, icon: 'icon-warning-sign'});

page_initor('dodebug', function(){
	$.getJSON("debuging?action=alltypes", function(rsp){
		if(rsp && rsp.respon === 'success'){
			let ops = rsp['types'].split(',');
			let seler = $("#testtype");
			seler.empty();
			for(let i=0,len=ops.length;i<len;i++){
				seler.append(`<option value="${ops[i]}">${ops[i]}</option>`);
			}
			document.getElementById("testtype").selectedIndex = -1;
		}
	});
});
page_collector.inner_functions={
	renew_form: function(formdata){
		let kn = formdata['reqtype'];
		page_collector.$('reqtype', kn);
		let fieldstr = formdata['reqkeys'];
		let that = $("#debug_form");
		let fields = fieldstr === ""?[]:fieldstr.split(',');
		that.empty();
		that.append(`<p>${formdata['requrl']}</p>`);
		for(var i=0,len=fields.length;i<len;i++){
			let row = `<div class="form-group"><label for="${fields[i]}">${fields[i]}</label><input type="text" class="form-control"  name="${fields[i]}"></div>`;
			that.append(row);
		}
	},
}
page_collector.bind_ini('dodebug', function(){
	$("#testtype").on('change', function(){
		$.getJSON("debuging?testtype=" + this.value, function(rtdata){
			if (rtdata && rtdata['reqtype']){
				page_collector.$("requrl", rtdata['requrl']);
				page_collector.inner_functions.renew_form(rtdata);
			}
		});
	});
	$("#dotest").on('click', function(){
		dlg_mgm.go_submit('dodebug');
	});
});

page_collector.bind_ini('allusers', function(){
	// usertype: 1-student, 2-teacher
	let get_pd_path = _exec.make_urlparam({action: 'listusers', usertype: 2, departid: 1, level: 1}, '/debuging');
  $("#ulister").stable({
    source_url: get_pd_path, 
    tbl_bar: '#ulister_bar',
    page_limit: 20,
    autoload: true,
    row_tmpl: '<tr rowid="${row.rownum}" data-departid="${row.departid}"><td>${row.cellphone}</td><td>${row.gender}</td><td>${row.ic_card_id}</td><td>${row.join_date}</td><td>${row.name}</td><td>${row.wxuserid}</td><td>${row.userid}</td><td><button class="btn btn-sm putmsg" type="button">MSG2</button><button class="btn btn-sm setacc" type="button">ASSIGN</button></td></tr>',
    innerbtn_actions: [
			['sendmsg2user', 'putmsg', function(r){
				cwxu = r.cells[5].innerText;
				msg = prompt("What you want to say?","");
				$.post("/switcher?action=sendmsg2user", {wxuserid: cwxu, content: msg}, function(rsp){
					if (rsp.respon == 'success'){
						imsger.show("OK");
					}else{
						emsger.show(JSON.stringify(rsp));
					}
				});
			}],
			['accountbindding', 'setacc', function(r){
				//no need now
				let cur_teacher = {name: r.cells[4].innerText, userid: r.cells[6].innerText, departid: r.dataset.departid};
				page_collector.$("cur_teacher", cur_teacher);
				alert(JSON.stringify(cur_teacher));
			}]
		]
  });
});

dlg_mgm.dlgs['dodebug'] = {
  did: '#dodebug',
  fid: '#debug_form',
  sma: function(did){
    let rta = dlg_mgm.get_json('#debug_form');
    if(rta){
			url = '/debuging?requrl=' + page_collector.$("requrl") + '&reqname=' + page_collector.$("reqtype");
      dlg_mgm.post_form('dodebug', rta, url);
    }else{
      alert('未知错误！');
    }
  },
  spa: function(rsp){
    if(rsp.respon === 'success'){
      //rsp:name//account
      rdata = rsp.data;
    }else if(rsp.respon === 'error'){
			emsger.show("错误");
		}else{
      document.getElementById('debuginfo').innerText=JSON.stringify(rsp);
    }
  }
}

dlg_mgm.dlgs['asstearcher'] = {
  did: '#dlg_ass_teacher',
  fid: '#frm_ass_teacher',
}