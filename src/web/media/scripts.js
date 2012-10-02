$(document).ready(function(){ 

    $("#smb").on('click', function() {
        //$(document).load(".");
        //alert('here');
        var $content_code = $('#wrapper_code').html();
          $.ajax({
            type: 'POST',
            url: '/proj/',
            data: {'wrapper_code':$content_code},
            success: function(data){
                //$('#main_content')[0].innerHTML = data;
                $('#main_content').html(data);
            }
        });
    })


    var click_drag = function(){
        $(".CodeMirror").css('z-index','3');
        $(this).css('z-index','4');
    };
    $('.id-script').on('click', function(){
        var hexsha = $(this).parent().parent().find('#version-t div').html();
        alert(hexsha)
        var path = $(this).parent().parent().find('#repository-t div').html();
        var scrName = $(this).html();
        var nbWind = $('.resizable').length;
        $.ajax({
          type: 'GET',
          url: 'nolabel/datafile',
          data: {'digest':hexsha, 'show_script':true, 'path':path},
          async: false
        }).done(function(data) {  
            id = ['code_wind',nbWind].join('');
            $el = $('<div/>', {
                id: id,
                class: 'resizable'
            });

            $el.appendTo('#wrapper_code');
             var editor = CodeMirror(document.getElementById(id), {
                mode: {name: "python",
                       version: 2,
                       singleLineStringErrors: false},
                lineNumbers: true,
                indentUnit: 4,
                tabMode: "shift",
                matchBrackets: true
              });
            editor.setOption("theme", "ambiance"); 
            //this way we hide the element. CodeMirrow is the new div.   
            $('.resizable').css('display','block')
                           .css('height','0px')
                           .css('width','0px');  
            editor.setValue(data);
            editor.refresh();
            $(".CodeMirror").draggable({handle:"div.ui-widget-header", snap: true});
            $(".CodeMirror").resizable();
         
            $('.headercode').bind('dblclick', function(){ 
                var $el_clicked = $(this).parent().parent();
                var $content = $el_clicked.find('.CodeMirror-scroll');
                if ($content.is(':hidden')){
                    $content.show();
                }else{
                    $content.hide();
                }
            });

            $el.find('.headercode').html(scrName + ': ' +hexsha);
            $(".CodeMirror").bind('drag', click_drag);
            $(".CodeMirror").bind('click', click_drag);
        });    
    });


    $('ol').listsorter();    
    $(document).click(function(){ // deselect all the rows of click is out of table
        $('.record').removeClass('activeRow');
    });
    //$('ol>li').click(function(event){
    $("ol>li").on('click', function(e) {
        e.preventDefault();
        return false;
    });
    //$('.record').click(function(e){
    
    if ('{{settings.display_density}}'=='condensed'){
        $('.record').css('line-height','14px');   
    }else{
        $('.record').css('line-height','32px');
        $('.label').css('font-size','18px');
    }
    
    $('input[type="radio"]').attr('checked', false);

    $('.t-item').click(function(){
        var $checked = $('input[type="radio"]:checked');
        var idrow = ['','.', $(this).attr('id').split('-')[1]].join('');
    });
    
    
    if ($(location).attr('href').indexOf('?n=true') != -1){
        $('#table_out tbody tr:eq(0) td').effect("highlight", {}, 15000); 
    }

    $('.simulations td').live('click', function(){
        if (!$(this).children().is('a')){
            $parent = $(this).parent();
            var $label = $parent.find('.Label-t').html();
            window.open(["/{{project_name}}", $label, ""].join('/'));
        }
    });

    $('#search_but').click(function(){
        $('#search_form').trigger('submit');
    });
            
    nbRecPerPage_changed = false;
    $('.modal').modal().modal('hide');
    $('.page.gradient').not('.inactive').mouseenter(function(){
        $(this).children().css('opacity','1.0');
    }).mouseleave(function(){
        $(this).children().css('opacity','0.5');
    });
    
    $('#input_nrec, #s_nbt').click(function(event){  
        nbRecPerPage_changed = true;
        event.stopPropagation();
        $(this).css('display','none');
        $('#s_nbt').css('display','block');     
    });
    
    $('html').click(function(){ 
        var $val = $('#s_nbt').val(); 
        if ($val > 0){    
            $('#input_nrec').css('display','block').html($val);
            $('#s_nbt').css('display','none');
            $('#s_nbt').removeClass('err_border');
            if ($('#myTab li.active a').attr('href') == '#second'){
                $('#save_set').removeClass('disabled');
            }
        }else{
            $('#s_nbt').addClass('err_border');
            $('#save_set').addClass('disabled');
        }   
    });

    $('#btn_run, #close_newrec').click(function(e){
        $('#mod_newrec').modal('hide');    
    });

     // new record popup:
     $(document).on('keyup keydown', function(e){
      if (e.which == 13){
            if ($('#mod_newrec').css('display')=='block'){  // new record popup
                if (e.type == "keydown"){
                    $('#btn_run').addClass('active');
                    e.preventDefault();
                }else{
                    $('#btn_run').removeClass('active');
                    $('#btn_run').trigger('click');
                }  
            }else if ($('#menu_search').css('display') == 'block'){  // search dropdown
                if (e.type == "keydown"){
                    $('#search_but').addClass('active');
                    e.preventDefault();
                }else{
                    $('#search_but').removeClass('active');
                    $('#search_but').trigger('click');
                }
            }
        }
    });
    
    $('#btn_newrec').click(function(){
        $.ajax({
          type: 'POST',
          url: '/{{project_name}}/settings',
          data: {'sumatra':true},
          async: true,
          dataType: 'json'
        }).done(function(data) {
             $('#mExec').val(data.execut);
             $('#mFile').val(data.mfile);     
        });
    });
    
    $('#menu_datewith > li').click(function(){
        $('#menu_datewith').hide();
        $('#sdate').text($(this).text());       
    });
    
    $('#idatewith, #up_icon, #low_icon').click(function(event){
        event.stopPropagation(); 
        $('#menu_datewith').show();
        $('#menu_datewith').offset({left: $('#idatewith').offset().left});
    });
    
    //$('.date').datepicker();
    $(".chzn-select").chosen();
    $(".chzn-select-deselect").chosen({allow_single_deselect:true});
    
    // #menu_search will inherit the offsetLength from this div
    $('#div_menu_search').offset({left: $('#text_subnav').offset().left+20});
    
    $('#icon_cdown').tooltip({
        title: 'show search options',
        placement: 'bottom'
    });
    
    $('#icon_cdown').mouseenter(function(){
        $(this).css('opacity','1.0');
    }).mouseleave(function(){
        $(this).css('opacity','0.2');
    }).click(function(event){   
        var parentWidth;
        parentWidth = $('input.span5')[0].offsetWidth - 2;
        $('#menu_search').css('width', parentWidth)
                         .show();
    });
    
    // prevent closing the search menu when clicking on it
    $('#menu_search, #icon_cdown, #ui-datepicker-div').click(function(event){
        event.stopPropagation(); 
        $('#menu_datewith').hide();
        return false; 
    });
    
    $('#close_menu, html').click(function() {
        $('#menu_search').hide();
        $('#menu_datewith').hide();
    });
     
    $('#pagin_info').dropdown();
   
    $('#li_settings').click(function(){
        $.ajax({
          type: 'POST',
          url: '/{{project_name}}/settings',
          data: {'web':true},
          async: true,
          dataType: 'json'
        }).done(function(data){
            $(['#button',data.display_density].join('_')).addClass('active_settings_row');
        });
    });
    
    //$('#table_out').tablesorter(); // use tablesorter.min.js
    
    $('#close_set, #close_set.btn').click(function(){
        $('#setModal').modal('hide');
    });
    
    /* Automatic check/uncheck of #Script and #Executable */
    $(".check-item").click(function(){   // any checkbox in settings window         
        /* #Script and #Executable have childrens, so if at least one of the chilrens is checked,
           the parents checkboxes will be checked automatically. */
        if ($(this).attr('id') != 'Script' && $(this).attr('id') != 'Executable'){
            if ($('.check-item.Executable:checked').length == 0){
                $('#Executable').attr('checked',false);
            } else{
                $('#Executable').attr('checked',true);
            };
            
            if ($('.check-item.Script:checked').length == 0){
                $('#Script').attr('checked',false);
            }else{
                $('#Script').attr('checked',true);
            }
        }else if ($(this).attr('id') == 'Executable'){
            if ($(this).attr('checked')=='checked'){
                $('.Executable').attr('checked',true);
            }else{
                $('.Executable').attr('checked',false);
            }
        }else if ($(this).attr('id') == 'Script'){
            if ($(this).attr('checked')=='checked'){
                $('.Script').attr('checked',true);
            }else{
                $('.Script').attr('checked',false);
            }
        };

        // if no checkboxes are checked the button 'save settings' will be disables 
        if ($(".check-item:checked").length == 0){
            $('#check_selectAll').attr('checked', false);
            $('#save_set').addClass('disabled');
        }else{
            $('#save_set').removeClass('disabled');
        }
        
    }); /* End of automatic check/uncheck of #Script and #Executable */
    
    $('#save_set').click(function(){ // button save settings 
            var UncheckedItems = new Array();
            if (!$('#save_set').hasClass('disabled')){          
                Exec_colspan = $('.Executable:checked').length;    
                Script_colspan = $('.Script:checked').length;
                $('.Script-t').attr('colspan', Script_colspan);
                $('.Executable-t').attr('colspan', Exec_colspan);
                
                // hide columns:
                $(".check-item").not(':checked').each(function() { 
                    $unchecked = $(this).attr('id');
                    $(['.', $unchecked, '-t'].join('')).hide();
                    UncheckedItems.push($unchecked);
                });
                
                // show columns:
                $(".check-item:checked").each(function() { 
                    $checked = $(this).attr('id');
                    $(['.', $checked, '-t'].join('')).show();
                });
                
                var nb_rec = $('#s_nbt').val();
                // save settings to .smt/project
                $.ajax({
                  type: 'POST',
                  url: '/{{project_name}}/settings',
                  data: {'table_HideColumns':UncheckedItems,
                         'nb_records_per_page':nb_rec,
                         'cols_span_execut':Exec_colspan,
                         'cols_span_script':Script_colspan,
                         'saveSettings':true},
                  async: true
                }).done(function(data){
                    if (nbRecPerPage_changed)
                        location.reload();
                });
            }
    });
    
    /* selection of all checkboxes */
    $("#check_selectAll").click(function() { 
        var checkedStatus = this.checked;
        
        $(".check-item").each(function() {
            this.checked = checkedStatus;
        });  
        
        if (!checkedStatus){
            $('#save_set').addClass('disabled'); // in case all are unchecked
        }else{
            $('#save_set').removeClass('disabled');
        }    
    });
    
    /* Settings->Display density->compact */
    $('.menu-rsettigns').not('#button_settings').click(function(){
        var $density_set = $(this).attr('id').split('_')[1]; // 'null' (=default) or 'condensed'
        
        $(this).addClass('active_settings_row');
            $.ajax({
              type: 'POST',
              url: '/{{project_name}}/settings',
              data: {'display_density':$density_set,
                     'saveSettings':true},
              async: true
            });

        if ($density_set == 'condensed'){
            $('.record').css('line-height','14px');
            $('.label').css('font-size','14px');
            //$('#table_out').addClass('table-condensed');
            $('#button_null').removeClass('active_settings_row');   
        }else{
            $('.record').css('line-height','32px');
            $('.label').css('font-size','18px');
            //$('#table_out').removeClass('table-condensed');
            $('#button_condensed').removeClass('active_settings_row');    
        }        
    });
      
   $('#button_settings').click(function(){
        var data;
        $('.check-item').attr('checked',true); // if before user has unchecked one and didn't save
        data =  $.ajax({type: 'POST',
                        url: '/{{project_name}}/settings',
                        async: false,
                        data: {'web':true},
                        dataType: 'json'});
        data = $.parseJSON(data.responseText);
        hiddenCols = data.table_HideColumns;
        if (hiddenCols){
            for (var item, i = -1; item = hiddenCols[++i];){
                $(['#', item].join('')).attr('checked',false);
            }
        }
    });
    
    $('#btn_run').click(function(){
        var $clone;
        $.fancybox.showActivity();
        $.ajax({
          type: 'POST',
          url: '/{{project_name}}/simulation',
          async: true,
          data: {'label':$('#mLabel').val(),
                 'reason':$('#mReason').val(),
                 'tag':$('#mTag').val(),
                 'execut':$('#mExec').val(),
                 'main_file':$('#mFile').val(),
                 'args':$('#mArg').val()
                },
          dataType: 'json'
        })
    }); 
});   