$(document).ready(function(){
    // jQuery UI Dialog    

    $('#dialog').dialog({
        autoOpen: false,
        width: 400,
        modal: true,
        resizable: false,
        buttons: {
            "Yes": function() {
                var url = window.location.pathname + $('form[name=actions]').attr('action')
                //console.log(url)
                $.post(url, {'delete': true}, function(data, textStatus){
                        $(this).dialog("close");
                        window.location.href = "..";
                    });
            },
            "No": function() {
                $(this).dialog("close");
            }
        }
    });

    $('form input[name=delete]').click(function(e){
        //e.preventDefault();
        $('#dialog').dialog('open');
        return false;
    });

});
