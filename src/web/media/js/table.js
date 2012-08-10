function labelList(tag, div_list){
    var $selected_labels = [],
        $selected_tags = [],
        list = {'labels':[], 'tags':[]};
    $('.record.ui-selected').each(function(){
        var $labl = $(this).find('#label-t a').html();     
        $selected_labels.push($labl);
        div_list.append('<span class="label">'+ $labl +'</span>');  
        if (tag){
            $(this).find('#tag-t a').each(function(){
                var $tag = $(this).html();
                if ($selected_tags.indexOf($tag) == -1) $selected_tags.push($tag);    
            }); 
        };
    });
    if (tag) {list['labels'] = $selected_labels, list['tags'] = $selected_tags}
    else list['labels'] = $selected_labels;
    return list;
};

function headerSearch(){
    var obj = {};
    var search_subnav = $('#search_subnav').val().split(','); // header of the page: search textarea
    search_subnav.forEach(function(property) {
        var tup = property.split(':');
        obj[tup[0]] = tup[1];
    });
    return obj;
};

$(function() {
    // add arrows which is used for indicating the order of sorting
    $('label.head-item').append("<span class='s-arrow'><span id='up' class='arr-s'>&#x25B2;</span><span id='down' class='arr-s'>&#x25BC;</span></span>");

    // initialization of the sorting for the ol
    $('#ol-content').listsorter(); 

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

    //this for preventing the deselection of records in the table (see record_list.html: (window).click())
    // #d-delete, #d-tags, #d-comp: the buttons  
    $('#d-delete, #d-tags, #d-comp, .modal').live('click', function(e){
        if (e.target.type !== 'checkbox'){ //delete_record.html has a checkbox and we don't want to make it unselectable
            e.preventDefault();
            return false;
        };
    });

    // click on the 'edit tags' button
    $('#d-tags').live('click', function(){
        var $div_list = $('#list-labels').empty();
        var tag = true;
        list = labelList(tag, $div_list);
        var $selected_labels = list.labels;
        var $selected_tags = list.tags;
        $('#form-tags #id_tags').val($selected_tags.join(', '));
        $selected_labels = $selected_labels.join(',');
        $('#arrLabls').append($selected_labels); // as soon as form is submitted we'll read this div to retrieve all the labels
    });

    //click on the 'compare simulations' button
    $('#d-comp').live('click', function(){ 
        var $div_list = $('#alist-labels').empty();
        var names_div = ['left', 'right'];
        list = labelList(false, $div_list);
        var $selected_labels = list.labels;
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

    // when paginate the results
    $('.page').not('.inactive').click(function(){
        $('.page').tooltip('hide');
        var $thisId = $(this).attr('id'),
            obj = {},
            $page;
        var search_header_obj =  headerSearch();
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
            date_interval: $('#sdate').html(), date_interval_from: $('#id_datewithin').val(), search_input: search_header_obj},
            success:function(data){
                $('#innerContent').html(data);
            }
          });
    }); 

    // quick pagination: drop-down list with the links 'newest' and 'oldest' simulations
    $('.quick-pag').click(function(){
        var $this = $(this).html();
        var search_header_obj =  headerSearch(); // search textarea in the header
        if ($this == 'Newest'){
            $page = 1;
        }else{
            $page = 1e+10; // some large number
        };
          $.ajax({
            type: 'POST',
            url: '.',
            data: {'page':$page, search_input:search_header_obj},
            success:function(data){
                $('#innerContent').html(data);
            }
          });
    });

    // when dragging the popup window with the script code, the dragged item is always above the all over popups
    var click_drag = function(){
        $(".CodeMirror").css('z-index','3');
        $(this).css('z-index','4');
    };

    // clicking the link with the script name: popup window with the code will be opened
    // (code is retrieved from the version control repository)
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
    
    // change the style of the pagination button when hover
    $('.page.gradient').not('.inactive').mouseenter(function(){
        $(this).children().css('opacity','1.0');
        $('.CodeMirror').css('opacity','0.3');
    }).mouseleave(function(){
        $(this).children().css('opacity','0.5');
        $('.CodeMirror').css('opacity','1.0');
    });

    //$("ol>li").on('click', function(e) {
    //    e.preventDefault();
    //    return false;
    //});


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

    // clicking on the record link
    $('.href_lab').click(function(e){
        e.stopPropagation();
        $(this).attr('href', window.location.pathname + $(this).html() + '/');
    });

    // clicking on the arguments link
    $('.href_args').click(function(e){
        var label = $(this).parent().parent().find('#label-t a').html();
        $.ajax({
            type: 'POST',
            url: label + '/',
            data: {'show_args':true},
            success:function(data){
                alert(data);
            }
        });
    });

    $('#btn_search').click(function(){
        var inquiry = $('#search_subnav').val();
        $('#main_content').load('search', {'search_inquiry':inquiry});
    });
});