$(function() {
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
        $('.CodeMirror').css('opacity','0.3');
    }).mouseleave(function(){
        $(this).children().css('opacity','0.5');
        $('.CodeMirror').css('opacity','1.0');
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
  
});