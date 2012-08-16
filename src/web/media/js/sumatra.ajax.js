$(function() {
    // initialization of the sorting for the ol
    $('#ol-content').listsorter(); 

     // initialization of the drop-down search list (#div_menu_search)
    $('#div_menu_search').offset({left: $('#search_subnav').offset().left}); // x-position as for the #search_subnav + 20px

    // this dropdown contains the links to the newest/oldest record sets
    $('#pagin_info').dropdown();

    // in case of hovering the pagination buttons (newer/older)
    $('.page.gradient').tooltip({
        title: function(){return $(this).attr('id');},
        placement: 'bottom',
        trigger: 'hover'
    });

    // hovering the repository name in table
    $('#repository-t span').tooltip({
        title: function(){return $(this).parent().parent().find('#repo-hid').html()},
        placement: 'right',
        trigger: 'hover'
    });

    // hovering the hex version
    $('#version-t span').tooltip({
        title: function(){return $(this).parent().parent().find('#version-hid').html()},
        placement: 'right',
        trigger: 'hover'
    });

    // as strings 'executable name' and 'executable version' are rather long, we used this hack for the nice rendering
    $('#l-eversion, #l-ename').each(function(){
        if ($(this).height() > 20){ // in case it spans one line
            $(this).css('margin-top', '0px');
        };
    });

    $('.record').on('mouseenter', function(){$(this).not('.ui-selected').addClass('hoverRow')})
                .on('mouseleave', function(){$(this).removeClass('hoverRow')});   

    // clicking on the arguments link
    $('.href_lab').on('click', function(e){
        e.stopPropagation();
        $(this).attr('href', window.location.pathname + $(this).html() + '/');
    });  
    
    $('.href_args').on('click', function(e){
        var label = $(this).parent().parent().find('#label-t a').html();
        $.ajax({
            type: 'POST',
            url: label + '/',
            data: {'show_args':true},   
            success:function(data){
                alert(data); // by now it is alert. TODO: stick the content to the window
            }
        });
    }); 

    // change the style of the pagination button when hover
    $('.page.gradient').not('.inactive').mouseenter(function(){
        $(this).children().css('opacity','1.0');
    }).mouseleave(function(){
        $(this).children().css('opacity','0.5');
    });  

    // using jquery-ui for the rows of the table
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

    // add little arrows which are used for indicating the order of sorting
    $('label.head-item').append("<span class='s-arrow'><span id='up' class='arr-s'>&#x25B2;</span><span id='down' class='arr-s'>&#x25BC;</span></span>");
    
    $('.id-script').on('click', function(){
        var click_drag = function(){
            $(".modalcode").css('z-index','3');
            $(this).css('z-index','4');
        };
        //$('#modal-code').modal('show');
        $li = $(this).closest('li');
        var hexsha = $li.find('#version-hid').html();
        var path = $li.find('#repo-hid').html();
        var label = $li.find('#label-t a').html();
        var scrName = $(this).html();
        var nb_wind = $('#wrapper_code').children().length;
        $.ajax({
          type: 'POST',
          url: label + '/',
          data: {'digest':hexsha, 'show_script':true, 'path':path}
        }).done(function(data) { 
             var modal_id = 'modal-code' + nb_wind,
                 code_id = 's-code' + nb_wind;

             $modal = '<div class="modal modalcode" id=' + modal_id + '>\
                      <div class="modal-header">\
                        <button type="button" class="close" data-dismiss="modal">×</button>\
                        <h3>'+ scrName + ': ' + hexsha +'</h3>\
                      </div>\
                      <div class="modal-body">\
                        <div id=' + code_id + '></div>\
                      </div>\
                    </div>';
             $('#wrapper_code').append($modal);
             //$('#s-code').empty();
             var editor = CodeMirror(document.getElementById('s-code' + nb_wind), {
                mode: {name: "python",
                       version: 2,
                       singleLineStringErrors: false},
                lineNumbers: true,
                indentUnit: 4,
                tabMode: "shift",
                matchBrackets: true
              });
            editor.setOption("theme", "ambiance");
            editor.setValue(data);
            $(".modalcode").draggable({handle:".modal-header", snap: false});
            $('.modalcode').modal({keyboard: false, backdrop:false});
            $('.close').on('click', function(){
                $closed = $(this).closest('.modal').attr('id');
                $('#' + $closed).empty();
            });
            $(".modalcode").bind('drag', click_drag);
            $(".modalcode").bind('click', click_drag);
            var $height_code = $('#' + code_id).find('.CodeMirror-scroll').height();
            if ($height_code < 700) 
                $('#' + code_id).find('.CodeMirror').css('height', $height_code);
        });
    });
});