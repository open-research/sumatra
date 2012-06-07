// this function is for retrieving from .smt/project the columns that were hidden by user
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