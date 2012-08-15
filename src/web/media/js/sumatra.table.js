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

$(function() {
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
    $('.id-script').on('click', function(){
        $li = $(this).closest('li');
        var hexsha = $li.find('#version-hid').html();
        var path = $li.find('#repo-hid').html();
        var label = $li.find('#label-t a').html();
        var scrName = $(this).html();
        //var nbWind = $('.resizable').length;
        //alert(hexsha);
        $.ajax({
          type: 'POST',
          url: label + '/',
          data: {'digest':hexsha, 'show_script':true, 'path':path}
        }).done(function(data) { 
          alert(data);
        });
    });


    /*
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
    });  */
});