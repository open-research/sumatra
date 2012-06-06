$(window).ready(function(){
    $('#search_but').click(function(){     
        $.ajax({
          type: 'POST',
          url: 'search',
          async: true,
          data: {'label':$('#ilabel').val()},
          dataType: 'html'
        }).done(function(data){
            $('#table_out tbody').html('');
            $('#table_out tbody').html(data);
            hideColumns(hiddenColumns()); //hide the columns which were hidden by user
            $("#table_out").trigger("update");  // for tablesorter
        });
    });
});