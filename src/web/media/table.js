$(document).ready(function(){
    $('#ol-content').listsorter(); 
    $('#pagin_info').dropdown();
    $('.page.gradient').tooltip({
        title: function(){
            return $(this).attr('id');    
        },
        placement: 'bottom',
        trigger: 'hover'
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

    $('#alist-labels span.label').live('click', function(){   
        var nbSelected = $('span.label.label-success').length; 
        var names_div = ['left', 'right'];   
        if (!$(this).hasClass('label-success')) { // click on the record
            if (nbSelected == 2){ // if more than two      
                $('span.label.label-success:eq(0)').removeClass('label-success');  //remove it from the leftmost label
            }
            $(this).addClass('label-success');   // record is activated
            $('span.label.label-success').each(function(i, el){

                var $labl = $(el).html();        //label of the clicked record
                var buffer = [window.location.pathname, $labl , "/ ", "#info_record"];
                buffer = buffer.join('');
                $('#sim-' + names_div[i]).load(buffer);    
            });
        }else{
            $(this).removeClass('label-success');
            // delete the part of the window with unchecked label
            if ($('#sim-left #td_label').html() == $(this).html()){
                $('#sim-left').empty();
            } else { $('#sim-right').empty(); }
        }
    });

    $('#ol-content').selectable({
            stop: function() {
                var result = $( "#testdiv" ).empty();
                var $head_table = $('#head_t');
                nbSelected = $( "li.ui-selected").length;
                result.append(nbSelected);
                $head_table.empty();
                $head_table.append('<div id = "d-nbrec"></div>')
                           .append('<div id = "d-delete" data-toggle="modal" href="#deleteModal">delete records</div>')
                           .append('<div id = "d-tags" data-toggle="modal" href="#setTagsModal">edit tags</div>')
                           .append('<div id = "d-comp" data-toggle="modal" href="#compareSim">compare simulations</div>');
                $('#d-nbrec').html(nbSelected + ' records');
            }
    });

    $('.CodeMirror').css('opacity','1.0');

    $('.page').not('.inactive').click(function(){
        $('.page').tooltip('hide');
        var $thisId = $(this).attr('id'),
            $page;
        if ($thisId == 'newer'){
            $page = $('#next_page_number').html()
        }else if($thisId == 'older'){
            $page = $('#previous_page_number').html()
        }
          $.ajax({
            type: 'POST',
            url: '.',
            data: {'page':$page},
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
        var hexsha = $(this).parent().parent().find('#version-t div').html();
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