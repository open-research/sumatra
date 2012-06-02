$(window).ready(function(){
    $('td.Repository-t, td.S-Version-t').tooltip({
        title: function(){
            return $(this).children().html();    
        },
        placement: 'bottom'
    });
});