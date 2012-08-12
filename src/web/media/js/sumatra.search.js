function getSearchFormOb(){
    var $inputs = $('#search_form :input');
    var fulltext_inquiry = $('#search_subnav').val(); //inquiry out of search form: using only the #search_subnav input
    var values = {};
    var txt_inquiry = '',
        $val,
        text;
    if (fulltext_inquiry && fulltext_inquiry.indexOf(':') < 0){ // ignore here the search form: only the content of #search_subnav
        values['fulltext_inquiry'] = fulltext_inquiry;
    }else{
        $inputs.each(function() {
            $this = $(this);
        	$val = $this.val();
            if ($val){
                if ($this[0].firstElementChild){ // option element: executable/repository (in DB they are the ForeignKeys, so integers)
                    $options = $this.children();
                    $options.each(function(){
                        if ($(this).attr('selected')) text = $(this).html();
                    });
                }else{
                    text = $val;
                };
                
                if (this.name && this.name.indexOf('interval') < 0) {
                    values[this.name] = $val; 
                }else { 
                    this.name = 'interval: ' + $('#sdate').html() + ', base date'; 
                }
                // fill the #search_subnav. Example: user defined label = 777 in the search form. After it should print
    		    // 'label: 777' in the input textarea in the header of the page.  
    		    if (txt_inquiry) {txt_inquiry += ', ' + this.name + ': ' + text;}
    		    else {txt_inquiry += this.name + ': ' + text; }
            }
        });
        $('#search_subnav').val(txt_inquiry);
        values['date_interval'] = $('#sdate').html(); // date interval is out of form, so we add it explicitely:
        values['date_interval_from'] = $('#id_datewithin').val();
    }
    return values;
};

$(function() {
	// initialization of jquery-ui datepicker used in the seach drop-down list
    $( "#id_timestamp, #id_datewithin" ).datepicker();

    // initialization of the drop-down search list (#div_menu_search)
    $('#div_menu_search').offset({left: $('#search_subnav').offset().left}); // x-position as for the #search_subnav + 20px
    $('#icon_cdown').click(function(event){   
        var parentWidth = $('input.span5')[0].offsetWidth - 2; // the width of this drop-down equals the width of #search_subnav
        $('#menu_search').css('width', parentWidth).show();
        // if it is clicked, we flush the content of the search input:
        search_input_content = $('#search_subnav').val();
        if (search_input_content.indexOf(':') < 0){ // if it doesn't contain the inquiry originally went from search form
        	$('#search_subnav').val('');
        };
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
        var searchFormOb = getSearchFormOb();
        $('#innerContent').load('search', searchFormOb);
    });

    // as soon as user clicks the search button in the search drop-down list, the form will be submited
    $('#btn-search_form').click(function(){
        var searchFormOb = getSearchFormOb();    
        $('#innerContent').load('search', searchFormOb);
    });
});