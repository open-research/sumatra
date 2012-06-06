function hiddenColumns(){
    $.ajax({
      type: 'POST',
      url: 'settings',
      async: false,
      data: {'web':true},
      dataType: 'json'
    }).done(function(data) {   
        cols = data.table_HideColumns;  
    });
    return cols;
}

function hideColumns(cols){
    if (cols){
        for (var item, i = -1; item = cols[++i];){
            $(['.', item, '-t'].join('')).hide();
        }
    }
} 