function labelList(tag, div_list){
    var $selected_labels = [],
        $selected_tags = [],
        list = {'labels':[], 'tags':[]};
    $('.record.ui-selected').each(function(i){
        var $labl = $(this).find('#label-t a').html();     
        $selected_labels.push($labl);
        if (i < 2) {
            div_list.append('<span class="label label-success">'+ $labl +'</span>'); 
        }else{
            div_list.append('<span class="label">'+ $labl +'</span>'); 
        }       
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
        //var names_div = ['left', 'right'];
        list = labelList(false, $div_list);
        //alert(list.labels);

        $('#body-comp').load('nolabel/', {'compare_records':true, records: list.labels});
        $('#alist-labels').tooltip({
            title: 'Click the records you would like to compare',
            placement: 'bottom',
            trigger: 'hover'
        });
        /*
        $.ajax({
            type: 'POST',
            url: 'nolabel/',
            data: {'compare_records':true, records: list.labels},   
            success:function(data){
                //alert(data); // by now it is alert. TODO: stick the content to the window
                $('#comparison_framework').empty().append(data);
            }
        });
        //var $selected_labels = list.labels;
        
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
        }*/
    });    
});