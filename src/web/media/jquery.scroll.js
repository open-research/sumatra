$(document).scroll(function(){
    // If has not activated (has no attribute "data-top"
    if (!$('#head_t').attr('data-top')) {
        // If already fixed, then do nothing
        if ($('#head_t').hasClass('subnav-fixed')) return;
        // Remember top position
        var offset = $('#head_t').offset()
        $('#head_t').attr('data-top', offset.top);
    }

    if ($('#head_t').attr('data-top') - $('#head_t').outerHeight() <= $(this).scrollTop())
        $('#head_t').addClass('subnav-fixed');
    else
        $('#head_t').removeClass('subnav-fixed');
});