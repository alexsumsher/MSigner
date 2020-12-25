// login
_env = {}
var imsger = new $.zui.Messager('', {type: 'primary', time: 3000, icon: 'icon-bolt'});
var emsger = new $.zui.Messager('', {type: 'danger', time: 3000, icon: 'icon-warning-sign'});
const get_json = function(dlg, item_names, item_mode, sp_ids, fillvals, skip_space){
	// skip_space: if value is set to ""; ignore
	// data-value: 优先于value；通常展示为用户可读，但实际需要值是编号;主要用于text
	const gv = function(ipt){
		let _v;
		switch(ipt.type){
			case "text": _v = ipt.dataset.value || ipt.value;break;
			case "select-multiple": {
				let vlist = [];
				let sos = ipt.selectedOptions;
				for(let i=0,len=sos.length;i<len;i++){
					vlist.push(sos[i].dataset.value || sos[i].value);
				};
				_v = vlist.join(',');
			};break;
			//case "select-one":ipt.options[ipt.selectedIndex].value;
			case "radio": if(ipt.checked){_v = ipt.value};break;
			case "checkbox": if(ipt.checked){_v = ipt.value};break;
			default: _v = ipt.dataset.value || ipt.value;
		}
		return _v;
	}
	
	let tform = document.querySelector(dlg);
	if (!tform){
		return null;
	}
	var rta = {};
	var imode = 0;//0:default;1:item_name to collect;2:item_name to remove
	if(item_names instanceof Array && item_mode !== '-'){
		for(var i=0,len=item_names;i<len;i++){
			rta[item_names[i]] = null;
		}
		imode = 1;
	}else{
		tform.querySelectorAll('[name]').forEach((itm)=>{
			let name = itm.getAttribute('name');
			if(imode === 1 && rta[name] !== null){
			  // if imode===1, rta[name] should have been set to null,
			  // so when rta[name] !== null, it's no need to collect
			  return;
			}
			if(itm.nodeName === 'DIV'){
				let thisvar = [];
				itm.querySelectorAll('input').forEach((n)=>{
					var v = gv(n);
					if(v === '' && skip_space){
						//pass
					}else{
						thisvar.push(v);
					}
				});
				// not a input item, use getattribute mode
				if(thisvar.length>0){
					rta[name] = thisvar;
				}else if(skip_space){
					//pass
				}else{
					rta[name] = typeof(fillvals)==="object"?fillvals[name]:'';
				}
				return;
			}
			var v = gv(itm);
			if (rta[name]){
				//pass when already have value with the same name(avoiding Conflict)
			}else if(v){
				rta[name] = v || fillvals || fillvals[name];
			}
		});
		// if there is some item don't wannt to post
		if(item_names instanceof Array && item_mode === '-'){
			for(var i=0,len=item_names.length;i<len;i++){
				delete rta[item_names[i]];
			}
		}
	}
	//special target withou a [name] attribute
	if(sp_ids){
		var tv;
		[].concat(sp_ids).map(function(v, i){
			tv = tform.querySelector('#' + v).text();
			if(tv){rta[v] = tv}
		});
	}
	return rta;
}


page_initor('main_page', function(){});

_PGC.bind_ini("main_page", function(){
	$("#orgmgm_tbl").stable({
		source_url: '/resource/school?action=list', 
		filter_params: {},
		tbl_bar: '#orgmgm_bar',
		key_name: 'idx',
		last_id: 0,
		page_limit: 20,
		autoload: true,
		pagedata: [],
		filter_zoom: '#orgmgm_filter',
		prtmnt: (r)=>{
			return r;
		},
		row_tmpl: '<tr rownum="${row.idx}"><td>${row.rowid}</td><td>${row.title}</td><td>${row.status}</td><td>${row.extdata}</td><td><button class="btn btn-sm act1" type="button">修改</button><button class="btn btn-sm act2" type="button">详情</button><button class="btn btn-sm act3" type="button">x</button></td></tr>',
		innerbtn_actions: [
			['修改', 'act1', function(r){
				let sdata = $("#orgmgm_tbl").data("stable")['selections'];
				_PGC.$("cur_org_idx", sdata.idx);
				console.log(sdata);
				let dlgr = $("#dlg_schooldata");
				dlg_mgm.set_values(dlgr, sdata);
				dlgr.modal({show:true});
			}],
			['详情', 'act2', function(r){alert(r)}],
			['删除', 'act3', function(r){
				// clear data? no
				if(!confirm("确定要删除该组织？")){return;}
				$.post("/api/school?action=delete", {idx: r.getAttribute("rownum")}, function(rsp){
					if (rsp && rsp.success === 'yes'){
						$("#orgmgm_tbl").stable("go_page", 1, null, null, true);
					} else {
						emsger.show("执行失败");
					}
				}, 'json');
			}]
		]
	});
	// UI-ACTIONS
	_this = document.getElementById("main_page");
	_this.querySelector("#btn_add_org").addEventListener("click", function(evt){
		let dlgr = $("#dlg_schooldata");
		dlg_mgm.do_clear(dlgr);
		dlgr.modal({show:true});
	});
	_this.querySelector("#dlg_schooldata").querySelector(".go_submit").addEventListener("click", function(evt){
		let dlgr = $("#dlg_schooldata");
		let params = dlg_mgm.get_json(dlgr);
		$.post("/api/school?action=add", params, function(rsp){
			if(rsp && rsp.success === 'yes'){
				imsger.show("OK");
				$("#orgmgm_tbl").stable("go_page", 1, null, null, true);
				dlgr.modal("hide");
			} else {
				emsger.show("执行失败");
			}
		}, 'json');
	});
});
_PGC.bind_load("main_page", function(){
});


$(document).ready(function() {

});