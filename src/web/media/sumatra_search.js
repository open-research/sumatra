$(window).ready(function(){
    $('#search_but').click(function(){ 
        label = $('#ilabel').val();
        urlstr = ['search/',label].join('');    
        $.ajax({
          type: 'POST',
          url: urlstr,
          async: false,
          data: {'label':$('#ilabel').val()},
          dataType: 'html'
        }).done(function(data){
            http_str = window.location.href;
            indx_search = http_str.indexOf('search');
            if( indx_search != -1 ) {
                window.open([http_str.substring(0, indx_search), urlstr].join(''), '_parent');
            }else{
                window.open(urlstr,'_parent');
            }  
        });
    });
});