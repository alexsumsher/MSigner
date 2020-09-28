(function ($) {

  var page_bar = {
    curdiv: '',
    //filter_zoom: div's id, collect data
    filter_zoom: '',
    pagedatas: {},
    tmpls: {
      innerdiv: '<div class="input-group" tblpages="${pages}"><span class="input-group-btn">all:??</span></div>',
      innerbtns: '<span class="input-group-btn"><button class="btn btn-default tblbar_gofirst" type="button"><i class="icon icon-fast-backward"></i></button><button class="btn btn-default tblbar_gopre" type="button"><i class="icon icon-chevron-left"></i></button></span><input type="text" class="form-control tblbar_setpage" placeholder=""><span class="input-group-btn"><button class="btn btn-default tblbar_gopage" type="button"><i class="icon icon-check"></i></button><button class="btn btn-default tblbar_gonext" type="button"><i class="icon icon-chevron-right"></i></button><button class="btn btn-default tblbar_golast" type="button"><i class="icon icon-fast-forward"></i></button><button class="btn btn-default tblbar_refresh" type="button"><i class="icon icon-spin icon-refresh"></i></button><button class="btn btn-default tblbar_start" type="button"><i class="icon icon-bolt"></i></button></span><div class="input-group-btn"><button type="button" class="btn btn-default pagesize" tabindex="-1">20</button><button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" tabindex="-1"><span class="caret"></span><span class="sr-only">更多数量</span></button><ul class="dropdown-menu pull-right" role="menu"><li><a href="#">20</a></li><li><a href="#">50</a></li><li><a href="#">100</a></li></ul></div>'
    },
    assign: function(div){
      if($(div).length === 1){
        page_bar.curdiv = div;
        return page_bar;
      }else{
        return null;
      }
    },

    //create bar and bind actions
    create: function(div, pages){
      let $div = $(div || page_bar.curdiv);
      pages = pages || 0;
      let idiv = $(`<div class="input-group" tblpages="${pages}"><span class="input-group-btn">all:??</span></div>`);
      idiv.append(page_bar.tmpls.innerbtns);
      if(pages>0){
        idiv.find('input').attr('placeholder', '1 / ' + pages);
      }
      $div.empty().append(idiv);
      // if(pages>0){
        // page_bar.set_page(div, 1, pages);
      // }
      return page_bar;
    },

    checkme: function(div){
      let $div = $(div || page_bar.curdiv);
      if($div.prop('id')){
        return true;
      }else{
        return false;
      }
    },

    //destroy
    destroy: function(div){},

    set_page: function(div, pagenum, pages){
      var tobj = $(div || page_bar.curdiv);
      var pagebox = tobj.find('input');
      if(pagenum <= 1 && pages>0){
        tobj.find('> div').attr('tblpages', pagenum);
        pagebox.prop('placeholder', '1 / ' + pages);
        return pages;
      }
      if(pages && pages > pagenum){
        tobj.find('> div').attr('tblpages', pages);
      }else{
        var pages = parseInt(tobj.find('> div').attr('tblpages'));
      }
      if(tobj.length !== 1){
        return false;
      }
      if(!pages || pages < pagenum){
        return false;
      }
      // tobj.find('input').val(pagenum + ' / ' + pages);
      pagebox.prop('placeholder', pagenum + '/' + pages);
    },
  };

  var tbl_funcs = {
    clear: function(tbl_obj, keepheader){
			let tobj;
			if(typeof(tbl_obj) === 'string'){
				tobj = document.getElementById(tbl_obj);
			}
			let rows = tobj.tBodies[0].rows;
			keepheader = keepheader || true;
			if(rows.length > 0){
				//tobj.empty();
				let i = 0;
				if(keepheader){
					i = 1;
				}
				for(len=tobj.prop('rows').length;i<len;i++){
					rows[i].innerHTML === "";
				}
			}
    },

    addrows: function(tbl_obj, tmpl, rowsdata, prtmnt){
      if (!(rowsdata instanceof Array) || rowsdata.length <= 0){
		console.warn('no data to list in table!');
        return;
      }
      //tmpl: #{}
      const tbody = $(tbl_obj).find('tbody')[0];
		//we don't have to clear first
      let idx=0;
      if(typeof(prtmnt)==='function'){
        let row,rowstr;
        rowsdata.forEach((r)=>{
          row = prtmnt(r);
		  if (!row){
			  return;
		  }
          row['rownum'] = ++idx;
          if(!row['rowid']){row['rowid']=idx}
          rowstr = eval('`' + tmpl + '`');
		  tbody.append(rowstr);
        });
        return idx;
      }
	  // if no prompt
      rowsdata.forEach((row)=>{
        row['rownum'] = ++idx;
        if(!row['rowid']){row['rowid']=idx}
        rowstr = eval('`' + tmpl + '`');
		tbody.append(rowstr);
      });
      return idx;
    },
		
	setrows: function(tbl_obj, tmpl, rowsdata, prtmnt, checker){
		// upgrade without clear
		if (!rowsdata || rowsdata.length === 0){
			console.warn('no data to list in table!');
			this.clear();
			return;
		}
		//let tbody = $(tbl_obj).find('tbody');
		let tbody = tbl_obj instanceof jQuery?tbl_obj.find('tbody')[0]:tbl_obj.tBodies[0];
		//we don't have to clear first
		let idx = 0;
		//let prerows = tbody.prop('rows')?tbody.prop('rows').length:0;
		let trows = tbody.rows;
		let prerows = trows.length;
		let tr;
		if(typeof(prtmnt)==='function'){
			let row,rowstr;
			rowsdata.forEach((r)=>{
				row = prtmnt(r);
				if(!row){
					return;
				}
				row['rownum'] = idx + 1;
				if(!row['rowid']){row['rowid'] = idx + 1}
				rowstr = eval('`' + tmpl + '`');
				if(prerows > 0 && idx<prerows){
					trows[idx].outerHTML = rowstr;
					//tbody.prop('rows')[idx].outerHTML = rowstr;
				}else{
					tr = tbody.insertRow();
					tr.outerHTML = rowstr;
				}
				idx++;
			});
		}else{
			rowsdata.forEach((row)=>{
				row['rownum'] = idx + 1;
				if(!row['rowid']){row['rowid'] = idx + 1}
				rowstr = eval('`' + tmpl + '`');
				if(prerows > 0 && idx<prerows){
					//tbody.prop('rows')[idx].outerHTML = rowstr;
					trows[idx].outerHTML = rowstr;
				}else{
					//tbody.append(rowstr);
					tr = tbody.insertRow();
					tr.outerHTML = rowstr;
				}
				idx++;
			});
		}
		if(prerows>idx){
			let rows = tbody.rows;
			for(let i=idx;i<prerows;i++){
				rows[i].innerHTML="";
			}
		}
		return idx;
	},
	
	add_row: function($tbl_obj, pos, row, tmpl){
		var tbody = $tbl_obj.find('tbody')[0];
		// table rows = head + body rows
		let row_num = tbody.rows.length; // tBodies[0].rows = tbl.rows - 1
		if(row_num === 0){
			pos = 0;
		}else if(pos === -1 || pos > row_num){
			pos = row_num;
		}
		let tr = tbody.insertRow(pos);
		tr.outerHTML = eval('`' + tmpl + '`');
		return pos;
	},

    del_rows: function(tbl_obj, row_th, count){
		// row_th starts from 0
		if(row_th >= 0){
			let tbody = $(tbl_obj).find('tbody')[0];
			let rows = tbody.rows;
			let count = count || 1, rt = [];
			while(count > 0){
				rt.push(rows[row_th].getAttribute('rownum'));
				tbody.deleteRow(row_th);
				count--;
			}
			return rt;
		}
    },
	
	ui_arange: function($tbl_obj, col_idx, isdesc, converter, row_from, row_end){
		// 按照指定列[从0开始], 重新排列table行，仅对UI进行操作;
		// converter: 函数，给出则通过converter对col进行处理返回的数据为比较值[返回int]
		// isdesc：是否降序； row_from/row_end[未完成]
		const def_converter = (v) => {
			//v allways td.textContent
			let v2 = parseFloat(v);
			if(isNaN(v2)){
				return null;
			}
			return v2;
		}
		row_from = row_from || 0;
		converter = converter || parseFloat;
		let tbd = $tbl_obj.find('tbody')[0];
		if (!tbd){
			console.error("no table!");
			return;
		}
		let trows = tbd.rows;
		row_end = (row_end || 1000)>trows.length?trows.length:row_end;
		let source = [], ranger = [], node0;
		if (converter){
			for(let i=0,len=row_end-row_from;i<len;i++){
				source.push(converter(trows[i].childNodes[col_idx].textContent));
			}
		} else{
			for(let i=0,len=row_end-row_from;i<len;i++){
				source.push(trows[i].childNodes[col_idx].textContent);
			}
		}
		//console.log(source);
		if (isdesc){
			// 降序[返回convertor 返回null的，自动最下]
			for(let x,v,i=0,len=source.length;i<len;i++){
				v = source[i];
				if(v === null){
					ranger.push(null)
					continue
				}
				x = 0;
				for(let j=0,len2=source.length;j<len2;j++){
					if(v<source[j]){
						x++;
					}
				}
				ranger.push(x);
			}
		} else {
			for(let x,v,i=0,len=source.length;i<len;i++){
				v = source[i];
				if(v === null){
					ranger.push(null)
					continue
				}
				x = 0;
				for(let j=0,len2=source.length;j<len2;j++){
					if(v>source[j]){
						x++;
					}
				}
				ranger.push(x);
			}
		}
		//console.log(ranger);
		// take ranger [3,7,2,5,4,1,2....] like
		let arch_node,target;
		// rowIndex: starts with 1 becourse a header row exists; but trows allways starts with 0...
		let _trows = [...trows];
		for(let cc=0,i=0,len=ranger.length;i<len;i++){
			if(ranger[i] === null){
				break;
			}
			arch_node = trows[cc++];
			for(let j=0;j<len;j++){
				if (ranger[j] === i){
					target = _trows[j];
					if (target === arch_node){}else{
						console.log("switch on " + target.rowIndex + " before " + arch_node.rowIndex);
						tbd.insertBefore(target, arch_node);
					}
					break;
				}
			}
		}
	},
	
  };

  var methods = {
    init: function(options){
      this.each(function(){
        var tbl_obj = $(this);
        var settings = tbl_obj.data('stable');
        if(!settings){
          var defaults = {
			filter_zoom: '',
			filter_params: null,
			filter_func: null, // 对自动生成的params进行处理，返回最终的params用于产生get table data url
            row_tmpl: '',
            source_url: '', //from url get json data
			last_request: '',
			key_name: '',
			last_id: 0,
            tbl_bar: '',
            tbl_pages: 0, // count page
            tbl_cur_page: 0, // current page
            tbl_offset: 0,  // 1->last item index
            page_limit: 20,
            autoload: true, //after initial load data immediatly
            prtmnt: null, // row-data-formating:(row_data)=>{return new-row_data}
            pagedata: null, //VER+: set to object for arrange/re_sort
            after_gopage: null,
			selections: null,
			// sort
			sort_enable: false,
			sort_converters: null, // functions that use for covernting
            // head checkbox
            allsel_chkbx: null,
            assist_checker: null,
            // [[name, class, action], ...]
			extra_click: null,
            innerbtn_actions: []
          };
          settings = $.extend({}, defaults, options);
        }else{
          settings = $.extend({}, settings, options);
        }
        if(!settings.row_tmpl){
          var tmpl = '<tr rowid="#{row.rowid}">';
          for(var i=0,len=tbl_obj[0].rows[0].cells.length;i<len;i++){
            tmpl += '<td>#{row.cell_content}</td>';
          }
          tmpl += '</tr>'
          settings.row_tmpl = tmpl;
        }
		// action on table:
		// click on a row for single-selection
		tbl_obj.find("tbody").on('click', 'tr', {tbl: tbl_obj.attr('id'), act: settings.extra_click}, function(event){
			let tdata = $('#' + event.data.tbl).data('stable');
			if(tdata['curtr']){
				tdata['curtr'].classList.remove('active');
			}
			tdata['curtr'] = this;
			let idx = this.getAttribute('rownum');
			tdata['selections'] = tdata.pagedata[idx];
			this.classList.add('active');
			if(event.data.act){
				event.data.act(tdata['selections']);
			}
		});
        //bind actions to buttons
        for(var i=0,len=settings.innerbtn_actions.length;i<len;i++){
          var actset = settings.innerbtn_actions[i];
          if(actset[1].substr(0,1) === '#'){
            $(actset[1]).on('click', actset[2]);
          }else{
            tbl_obj.on('click', '.' + actset[1], {action: actset[2]},function(event){
              var trow = $(this).closest('tr')[0];
              // return the DOM tr not the jquery tr
              event.data.action(trow);
            });
          }
        }
		// filterzoom action on radio
		if(settings.filter_zoom && typeof(settings.filter_zoom)==='string'){
			$(settings.filter_zoom).on('click', 'input:radio', function(event){
				methods['go_page'](1, true, null, false, tbl_obj);
			});
		}
		// checkbox for all select
		if(settings.allsel_chkbx){
			$(settings.allsel_chkbx).on("click", function(){
				//test first row for checkbox
				let $table = $(this).closest("table");
				let checker = $table.data('stable').assist_checker;
				console.log(checker);
				if(this.checked){
					console.log('select all');
					$table.stable('toggle_checks', true, checker);
					//methods['toggle_checks'](true, settings.assist_checker);
				}else{
					console.log('unselect all');
					$table.stable('toggle_checks', false, checker);
					//methods['toggle_checks'](false, settings.assist_checker);
				}
			});
		}
        tbl_obj.data('stable', settings);
        //pagebar
        if(settings.autoload){
          methods['go_page'](1, true, null, false, tbl_obj);
        } else {
			tbl_obj.data('stable').pagedata = {};
		}
        if(settings.tbl_bar){
			// page_bar.assign(settings.tbl_bar).create('', settings.tbl_pages);
			$(settings.tbl_bar).on('click', 'button', {tbl: tbl_obj.attr('id')}, function(event){
				// tblbar_gofirst/pre/gopage/next/last
				var $stable = $('#' + event.data.tbl);
				var btc = this.getAttribute('class').split(/\s+/).pop();
				var cpage = $stable.data('stable')['tbl_cur_page'];
				var allpage = $stable.data('stable')['tbl_pages'];
				if(!allpage){
				  return false;
				}
				var topage = 0;
				switch(btc){
					case 'tblbar_gofirst': topage = cpage===1?0:1;
					break;
					case 'tblbar_gopre': topage = cpage>1?cpage-1:0;
					break;
					case 'tblbar_gonext': topage = cpage===allpage?0:cpage+1;
					break;
					case 'tblbar_golast': topage = cpage===allpage?0:allpage;
					break;
					case 'tblbar_gopage': {
						topage = parseInt($(this).closest('div').find('input').val()) || 0;
						topage = (topage>allpage || topage<1 || topage === cpage)?0:topage;
					};
					break;
					case 'tblbar_refresh': topage = cpage;
					break;
					case 'tblbar_start': {};
					break;
				}
				if(topage===0){
					$(this).closest('div').find('input').prop('placeholder', cpage + '/' + allpage).val('');
					return;
				}else{
					$(this).closest('div').find('input').prop('placeholder', topage + '/' + allpage).val('');
					$stable.stable('go_page', topage);
				}
			});
			// li of pagesize
			$(settings.tbl_bar).on('click', 'li', {tbl: tbl_obj}, function(event){
				let cont = this.innerText;
				this.parentElement.previousElementSibling.previousElementSibling.innerText = cont;
				tbl_obj.data('stable').page_limit = parseInt(cont);
			});
        }
      });
    },
		
	clear: function(tblobj, force){
		//update mode:
		tblobj = tblobj || $(this);
		if(tblobj.length === 0){
			return;
		}
		if(force){
			tbl_funcs.clear(tblobj);
			return;
		}
		let trows = tblobj.length?tblobj[0].tBodies[0].rows:tblobj.tBodies[0].rows;
		for(let i=0;i<trows.length;i++){
			if(trows[i].innerHTML !== ""){
				trows[i].innerHTML = '';
			}
		}
	},
    
    set_page_data: function(pagedata, sort_func){
		// pagedata pass in is array and convert to data-object to store
		//for debugging
		let tbl_obj = $(this);
		let cursetting = tbl_obj.data('stable');
		let _pagedata = {};
		let kn = cursetting.key_name;
		pagedata.forEach((n)=>{
			_pagedata[n[key_name]] = n;
		});
		//console.log(cursetting);
		tmpl = cursetting['row_tmpl'];
		//tbl_funcs.clear(tbl_obj);
		if (typeof(sort_func) === 'function'){
			pagedata = pagedata.sort(sort_func);
		} else if (typeof(sort_func) === 'string'){
			// inner sort key-name
			//;pass
		}
		tbl_funcs.setrows(tbl_obj, tmpl, pagedata, cursetting['prtmnt']);
		if(cursetting['tbl_bar']){
			page_bar.assign(cursetting['tbl_bar']).create(null, 1);
		}
		cursetting['tbl_pages'] = 1;
		cursetting['pagedata'] = _pagedata;
	},
		
	set_row: function(row_line, rowdata){
		//row_line: starts with 1
		let setting = tbl_obj.data('stable');
		let tbl_obj = $(this),
			tmpl = setting.row_tmpl,
			prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		if (!row){
			return false;
		}
		tbl_obj.find('tbody')[0].rows[row_line-1].outerHTML =  eval('`' + tmpl + '`');
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
		return row;
	},
	
	set_row_byid: function(keyid, rowdata){
		let tbl_obj = $(this);
		let setting = tbl_obj.data('stable');
		let pdata = setting.pagedata,
			keyname = setting.key_name,
			tmpl = setting.row_tmpl,
			prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		if (!row){
			return false;
		}
		let trows = tbl_obj.find('tbody')[0].rows
		for(let row_idx=0, rlen = trows.length;row_idx<rlen;row_idx++){
			if (trows[row_idx].getAttribute('rownum') == keyid){
				trows[row_idx].outerHTML =  eval('`' + tmpl + '`');
				console.log('set_row_byid: row text is set!');
				pdata[keyid] = rowdata;
				return;
			}
		}
		alert("set_row_byid: not found!");
	},
	
	del_row_byid: function(keyid){
		let tbl_obj = $(this);
		let setting = tbl_obj.data('stable');
		let pdata = setting.pagedata,
			keyname = setting.key_name;
		let trows = tbl_obj.find('tbody')[0].rows
		for(let row_idx=0, rlen = trows.length;row_idx<rlen;row_idx++){
			if (trows[row_idx].getAttribute('rownum') == keyid){
				trows[row_idx].outerHTML = "";
				console.log('del_row_byid: row text is done!');
				delete pdata[keyid];
				return;
			}
		}
		alert("del_row_byid: not found!");
	},

	del_row: function(start, len){
		// starts with 1
		if(start<1){
			return false;
		}
		start = start - 1;
		var max = this.tBodies[0].rows.length;
		len =  max - len - start > 0?len:max - start;
		let dels = tbl_funcs.del_rows(this, start, len, this.data('stable').key_name);
		if(dels.length > 0){
			let pd = this.data('stable').pagedata;
			dels.forEach((n)=>{
				delete pd[n];
			});
		}
    },
	
	get_row: function(arg, get_source, findby, not_scroll){
		// get a row
		// if get_source: get the source data from pagedata
		$tbl = this[0];
		let r,rm,rd;
		if (typeof(arg) === "number"){
			// row index
			r = $tbl.tBodies[0].rows[arg+1];
			rm = r.getAttribute('rownum');
		} else if (typeof(arg) === "string"){
			let rows = $tbl.tBodies[0].rows;
			let like_first=-1, match_first=-1;
			for (let i=0,len=rows.length;i<len;i++){
				r = rows[i];
				let cells = r.cells;
				for (let j=0,lenj=cells.length;j<lenj;j++){
					if (cells[j].textContent === arg && match_first === -1){
						match_first = i;
						break;
					}else if (like_first === -1 && cells[j].textContent.indexOf(arg) >= 0){
						like_first = i;
					}
				}
				if (match_first > -1){
					r = rows[match_first];
					break;
				}
			}
			if (match_first === -1 && like_first > -1){
				r = rows[like_first];
			}
		}
		if (!r){
			return;
		}
		if (!not_scroll){
			window.scrollTo(0, r.offsetTop);
		}
		r.click();
		if (get_source && findby){
			let pdata = $($tbl).data("stable")["pagedata"];
			for(let i=0,len=pdata.length;i<len;i++){
				if (pdata[i][findby] == rm){
					return pdata[i];
				}
			}
			return null;
		}
		return r;
	},
	
	append_row: function(rowdata){
		let setting = this.data('stable');
		let prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		tbl_funcs.add_row(this, -1, row, setting.row_tmpl);
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
    },
	
	insert_row: function(pos, rowdata){
		if(pos === 0){
			alert("row pos starts with 1");
			return false;
		}
		let setting = this.data('stable');
		let prtmnt = setting.prtmnt;
		let row = prtmnt(rowdata);
		tbl_funcs.add_row(this, pos-1, row, setting.row_tmpl);
		let idx = rowdata[setting.key_name];
		setting.pagedata[idx] = rowdata;
	},
	
	update_row: function(row){
		// update row by value
	},
    
    toggle_checks: function(check, checker){
      let tbody = this.length?this.find('tbody')[0]:this.tBodies[0];
      let rows = tbody.rows;
      if(rows[0].cells[0].firstElementChild.type !== 'checkbox'){
        return false;
      }
      if(check){
        checked = true;
      }else if(check === undefined){
        // when not set, auto reverse
        checked = 0;
      }else{
        checked = false;
      }
      for(let i=0,len=rows.length;i<len;i++){
        if(checker && !checker(rows[i])){
          continue;
        }
        if(checked === 0){
          checked = rows[i].cells[0].firstElementChild.checked?false:true;
        }
        rows[i].cells[0].firstElementChild.checked = checked;
      }
    },

    go_page: function(pagenum, summary, params, no_tbl_bar, iniobj){
		var tbl_obj = iniobj?$(iniobj):$(this);
		var pagenum = pagenum || 1;
		if (typeof(pagenum) === 'number'){
			var cursetting = tbl_obj.data('stable');
			var allparam = {page: pagenum, page_limit: cursetting['page_limit']};
			// collect filters
			let fz = cursetting['filter_zoom'];
			if (fz){
				if(typeof(fz) === 'string'){
					let cfs = dlg_mgm.get_json(fz, null, null, null, null, true);
					$.extend(allparam, cfs);
				}else if(typeof(fz) === 'object'){
					$.extend(allparam, fz);
				}
			}
			if(summary || pagenum === 1 || !cursetting['tbl_pages']){
				allparam['summary'] = 'yes';
				summary = true;
			}else if (cursetting['last_id'] > 0){
				allparam['last_id'] = cursetting['last_id'];
			}
			// if(cursetting['extkeys']){
			//   $.extend(allparam, cursetting['extkeys']);
			// }
			params = params || cursetting['filter_params'];
			if(params){
				//$.extend(allparam, params);
				Object.assign(allparam, params);
			}
			if(typeof(cursetting['filter_func']) === 'function'){
				let allparam = cursetting['filter_func'](allparam);
			}
			var url = _exec.make_urlparam(allparam, cursetting['source_url']);
			cursetting['last_request'] = url;
		}else if(pagenum === 'reflash'){
			var url = cursetting['last_request'];
			if(!url){
				return false;
			}
		}
		dout('gopage now', url);
		$.getJSON(url, function(rt, stat){
			if(!rt.data){
				console.warn("no data to list in table!");
				//clear(tbl_obj[0]);
				methods['clear'](tbl_obj);
				return false;
			}else if(rt.success && rt.success === 'no'){
				console.error("failure get data!\n" + rt.msg);
				return false;
			}
			///////////////////////// For Tencent smart school: using dataList&pageInfo
			let data = rt.data.dataList?rt.data.dataList:rt.data;
			let pinfo = rt.data.pageInfo?rt.data.pageInfo:{total: Math.ceil(rt.dlen/cursetting['page_limit'])};
			if(summary){
				if(pinfo.total){
					cursetting['tbl_pages'] = parseInt(pinfo.total);
				}else{
					cursetting['tbl_pages'] = 1
				}
				if (cursetting['tbl_bar'] && !no_tbl_bar){
					console.log('create toolbar');
					page_bar.create(cursetting['tbl_bar'], cursetting.tbl_pages);
					page_bar.set_page(cursetting['tbl_bar'], pagenum, cursetting.tbl_pages);
				}else {
					// just set page num
					page_bar.set_page(cursetting['tbl_bar'], pagenum, cursetting.tbl_pages);
				}
			}
			let kn = cursetting['key_name'];
			let _data = {};
			data.forEach((n)=>{
				_data[n[kn]] = n;
			});
			cursetting['pagedata'] = _data;
			tbl_funcs.setrows(tbl_obj, cursetting['row_tmpl'], data, cursetting['prtmnt']);
			cursetting['tbl_offset'] = cursetting['tbl_cur_page'] * cursetting['page_limit'] + data.length;
			if (cursetting['key_name']){
				let last_row = data[data.length - 1];
				cursetting['last_id'] = last_row[kn];
			}
			//tbl_funcs.clear(tbl_obj);
			//tbl_funcs.addrows(tbl_obj, cursetting['row_tmpl'], data, cursetting['prtmnt']);
			if(cursetting['after_gopage']){
				cursetting['after_gopage'](data);
			}
      });
      cursetting['tbl_cur_page'] = pagenum;
    },
  };

  $.fn.stable = function (options){
    var method = arguments[0];
    if(methods[method]){
      method = methods[method];
      Array.prototype.shift.call(arguments);
    }else if(typeof(method) === 'object' || !method){
      method = methods.init;
    }else{
      $.error('Method: ' + method + ' not exits!');
      return this;
    }
    //this === $(loader):
    return method.apply(this, arguments);
  };  
})(jQuery);