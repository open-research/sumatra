$(document).ready(function(){
    $('ol').listsorter(); 
    $('#pagin_info').dropdown();

    $('.page').not('.inactive').click(function(){
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

    if ($('#settings_table').html()=='condensed'){
        $('.record').css('line-height','14px');   
    }else{
        $('.record').css('line-height','32px');
        $('.label').css('font-size','18px');
    }

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


    $("ol>li").on('click', function(e) {
        e.preventDefault();
        return false;
    });

    $('.record').on({
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
        'mouseenter':function(){
        $(this).addClass('hoverRow');
        },
        'mouseleave':function(){
        $(this).removeClass('hoverRow');
        },
    });
});