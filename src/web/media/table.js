$(function() {
    $('label.head-item').append("<span class='s-arrow'><span id='up' class='arr-s'>&#x25B2;</span><span id='down' class='arr-s'>&#x25BC;</span></span>");

    $('#ol-content').listsorter(); 
    $('#pagin_info').dropdown();
    $('.page.gradient').tooltip({
        title: function(){
            return $(this).attr('id');    
        },
        placement: 'bottom',
        trigger: 'hover'
    });

    

    if ($('#l-eversion').height() > 20){ // in case it spans one line
        $('#l-eversion').css('margin-top', '0px');
    };

    if ($('#l-ename').height() > 20){ // in case it spans one line
        $('#l-ename').css('margin-top', '0px');
    };


    $('#d-delete, #y-delRec, #d-tags, #saveTags, #d-comp, #compareSim').live('click', function(e){
        e.preventDefault();
        return false;
    });

    $('#y-delRec').click(function(){
        var succ = false;
        deleteArr = new Array(); // records to delete
        $('li.ui-selected').each(function(){
            deleteArr.push($(this).find('#label-t').html())
        });
        $.ajax({
            type: 'POST',
            url: 'delete/',
            data: {'delete':deleteArr,'delete_data':true}, //presume that user always want to delete data
            success:function(data){
                succ = true;
            },
            async: false
        });
        if (succ){
            window.open('.','_self');
        }
    });

    $('#d-tags').live('click', function(){ // click on the 'edit tags' button
        var $div_list = $('#list-labels').empty();
        var $selected_labels = new Array();
        var $selected_tags = new Array();
        $('.record.ui-selected').each(function(){
            var $labl = $(this).find('#label-t').html();
            $(this).find('#tag-t a').each(function(){
                var $tag = $(this).html();
                if ($selected_tags.indexOf($tag) == -1) $selected_tags.push($tag);    
            });             
            $selected_labels.push($labl);
            $div_list.append('<span class="label">'+ $labl +'</span>');  
        });
        $('#form-tags #id_tags').val($selected_tags.join(', '));
        var $selected_labels = $selected_labels.join(',');
        $('#arrLabls').append($selected_labels); // as soon as form is submitted we'll read this div to retrieve all the labels
    });

    $('#d-comp').live('click', function(){ //click on the 'compare simulations' button
        var $div_list = $('#alist-labels').empty();   // !!! create function. reapeat the code for #d-tags
        var $selected_labels = new Array();
        var names_div = ['left', 'right'];
        $('.record.ui-selected').each(function(){
            var $labl = $(this).find('#label-t').html();           
            $selected_labels.push($labl);
            $div_list.append('<span class="label">'+ $labl +'</span>');  
        });
        if ($selected_labels.length == 2){ // if user choose exactly 2 records to compare     
            $('#rec-compare').empty();
            $('#alist-labels span').addClass('label-success'); 
            for( var i = -1, n = 2; ++i < n; ) {         
                var buffer = [window.location.pathname, $selected_labels[i], "/ ", "#info_record"];
                buffer = buffer.join('');      
                $('#sim-' + names_div[i]).load(buffer);
            }
        }else{
            $('.analysis-w').empty(); //clear the the content of the popup window if user choose more than 2 records
        }
    });

    $('#ol-content').selectable({
            filter: 'li:not("div")',  //select only li and not the children divs
            stop: function() {
                var result = $( "#testdiv" ).empty();
                nbSelected = $( "li.ui-selected").length;
                result.append(nbSelected);
                $('#default_header').css('display','none');
                $('#selection_header').css('display','block');
                $('#d-nbrec').html(nbSelected + ' records');
            }
    });

    $('.CodeMirror').css('opacity','1.0');

    $('.page').not('.inactive').click(function(){
        $('.page').tooltip('hide');
        var $thisId = $(this).attr('id'),
            $page;
        if ($thisId == 'newer'){  // views.py: list_records with ajax request
            $page = $('#next_page_number').html()
        }else if($thisId == 'older'){
            $page = $('#previous_page_number').html()
        }
          $.ajax({
            type: 'POST',
            url: '.',
            data: {'page':$page, executable:$('#id_executable').val(), repository:$('#id_repository').val(),
            tags:$('#id_tags').val(), main_file:$('#id_main_file').val(),
            label:$('#id_label').val(), script_arguments:$('#id_script_arguments').val(), reason:$('#id_reason').val(), timestamp:$('#id_timestamp').val(),
            date_interval: $('#sdate').html(), date_interval_from: $('#id_datewithin').val()},
            success:function(data){
                $('#innerContent').html(data);
            }
          });
    }); 

    $('.quick-pag').click(function(){
        var $this = $(this).html();
        if ($this == 'Newest'){
            $page = 1;
        }else{
            $page = 1e+10; // some large number
        };
          $.ajax({
            type: 'POST',
            url: '.',
            data: {'page':$page},
            success:function(data){
                $('#innerContent').html(data);
            }
          });
    });

    var click_drag = function(){
        $(".CodeMirror").css('z-index','3');
        $(this).css('z-index','4');
    };

    $('.id-script').on('click', function(){
        $li = $(this).parent().parent();
        var hexsha = $li.find('#version-hid').html();
        var path = $li.find('#repo-hid').html();
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
    
    $('.page.gradient').not('.inactive').mouseenter(function(){
        $(this).children().css('opacity','1.0');
        $('.CodeMirror').css('opacity','0.3');
    }).mouseleave(function(){
        $(this).children().css('opacity','0.5');
        $('.CodeMirror').css('opacity','1.0');
    });

    $("ol>li").on('click', function(e) {
        e.preventDefault();
        return false;
    });


    $('.record').on({
    /*
     'click': function(e) {
        if (e['ctrlKey']){
            if ($(this).hasClass('activeRow')){
                $(this).removeClass('activeRow');
            }else{
                $(this).addClass('activeRow');
            }
        }else if(e['shiftKey']){  // select the range of rows between two selected
            nb_selected = $('.activeRow').length;
            if (!nb_selected){   // select all
                $('.record').addClass('activeRow');
            }else{
                $selectedY = $('.record.activeRow').position()['top'];
                $clickY = $(this).position()['top'];
                if ($clickY >= $selectedY) {
                    $($('.record.activeRow')[0]).nextUntil($(this).next()).addClass('activeRow');
                }else{
                    $($('.record.activeRow')[0]).prevUntil($(this).prev()).addClass('activeRow');
                }
            }
        }
        else{
            $('.record').removeClass('activeRow');
            $(this).addClass('activeRow');
        }  
        },
        */
        'mouseenter':function(){
        $(this).not('.ui-selected').addClass('hoverRow');
        },
        'mouseleave':function(){
        $(this).removeClass('hoverRow');
        },
    });
});