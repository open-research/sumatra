function getSearchFormOb(){
    var $inputs = $('#search_form :input');
    var $fulltext_inquiry = $('#search_subnav').val(); //inquiry out of search form: using only the #search_subnav input
    var values = {};
    if ($fulltext_inquiry){ // ignore here the search form: only the content of #search_subnav
        values['fulltext_inquiry'] = $fulltext_inquiry;
    }else{
        $inputs.each(function() {
            if (this.name) values[this.name] = $(this).val();
        });
        values['date_interval'] = $('#sdate').html(); // date interval is out of form, so we add it explicitely:
        values['date_interval_from'] = $('#id_datewithin').val();
    }
    return values;
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
	// initialization of jquery-ui datepicker used in the seach drop-down list
    $( "#id_timestamp, #id_datewithin" ).datepicker();

    // initialization of the drop-down search list (#div_menu_search)
    $('#div_menu_search').offset({left: $('#search_subnav').offset().left + 20}); // x-position as for the #search_subnav + 20px
    $('#icon_cdown').click(function(event){   
        var parentWidth = $('input.span5')[0].offsetWidth - 2; // the width of this drop-down equals the width of #search_subnav
        $('#menu_search').css('width', parentWidth).show();
    });
    // user can close the drop-down search list by clicking on the window or by clicking #close_menu (little icon top-right side)
    $('#close_menu, html').click(function() {
        $('#menu_search').hide();
    });
    // prevent closing the drop-down search list when clicking on it
    $('#menu_search, #icon_cdown, #ui-datepicker-div').click(function(event){
        event.stopPropagation(); 
        $('#menu_datewith').hide();
        return false; 
    });

    // clearing of the search form fields
    $('#search_form').find(':input').each(function() {
         $(this).val('');
    });

    // search input textarea
    $('#search_subnav').val('');

    // as soon as user clicks the search button in the search drop-down list, the form will be submited
    $('#btn-search_form').click(function(){
        searchFormOb = getSearchFormOb()
        $('#main_content').load('search', searchFormOb);
    });

    // "date within"
    $('#menu_datewith > li').click(function(){
        $('#menu_datewith').hide();
        $('#sdate').text($(this).text());       
    });
    $('#idatewith, #up_icon, #low_icon').click(function(event){
        event.stopPropagation(); 
        $('#menu_datewith').show();
        $('#menu_datewith').offset({left: $('#idatewith').offset().left});
    });

	// clicking the button 'Search' in the header of the page
    $('#btn-search_header').click(function(){
        searchFormOb = getSearchFormOb()
        $('#main_content').load('search', searchFormOb);
    });
});