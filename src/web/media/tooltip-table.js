$(window).ready(function(){
    $('td.Repository-t, td.S-Version-t').tooltip({
        title: function(){
            return $(this).children().html();    
        },
        placement: 'bottom'
    });

    $('#icon_cdown').tooltip({
        title: 'show search options',
        placement: 'bottom'
    });
});