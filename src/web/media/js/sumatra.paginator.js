$(function() {
	// pagination of the results
    $("body").on("click", ".page:not(.inactive)", function(){
        $('.page').tooltip('hide');
        var $thisId = $(this).attr('id'),
            $page,
            searchFormOb = getSearchFormOb();
        if ($thisId == 'newer'){  // views.py: list_records with ajax request
            $page = $('#next_page_number').html()
        }else if($thisId == 'older'){
            $page = $('#previous_page_number').html()
        };
        searchFormOb['page'] = $page;
        $('#innerContent').load('.', searchFormOb);
    }); 

    // quick pagination: drop-down list with the links 'newest' and 'oldest' simulations
    $("body").on("click", ".quick-pag", function(){
        var $this = $(this).html(),
        	searchFormOb = getSearchFormOb();
        if ($this == 'Newest'){
            $page = 1;
        }else{
            $page = 1e+10; // some large number
        };
        searchFormOb['page'] = $page;
        $('#innerContent').load('.', searchFormOb);
    });
});