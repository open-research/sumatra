$(window).ready(function(){
    $('#search_but').click(function(){
        $.ajax({
          type: 'POST',
          url: 'search',
          async: true,
          data: {'label':$('#ilabel').val()},
          //dataType: 'json'
        }).done(function(data) {
            alert(data);
        }); 
    });
});