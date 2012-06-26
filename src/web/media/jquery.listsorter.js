(function ($) {
    $.extend({
            listsorter: new
            function(){
                var parsers = [];
  
                this.construct = function (settings) {
                    return this.each(function () {
                        var $this, $document, $headers, cache, config, shiftDown = 0, sortOrder;
                        this.config = {};
                        config = this.config;
                        $this = $(this);
                        // try to auto detect column type, and store in tables config
                        this.config.parsers = buildParserCache(this); 
                        parsers = this.config.parsers;
                        // build the cache for the tbody cells
                        cache = buildCache(this);
                        // click one of the headers of the table:
                        $('.t-item').click( 
                        function (e) {
                            var totalRows = cache.normalized.length;
                            if (totalRows > 0) {
                                // store exp, for speed
                                var $cell = $(this);
                                $cell[0].firstElementChild.style['visibility'] = 'visible'; //span containing the arrows becomes visible
                                $($cell[0].firstElementChild.children).toggle();
                                var arrows = $cell[0].firstElementChild.children;
                                for (var item, i = -1; item = arrows[++i];) {
                                    if (item.style.display != 'none') { // visible                                  
                                        this.order = (item.id == 'down') ? 0 : 1;                                
                                        break;
                                    }    
                                }
                                // flush the sort list
                                config.sortList = [];
                                config.sortList.push([0, this.order]);  //only the first column
                                setTimeout(function () {
                                        cache_sorted = multisort($this[0], config.sortList, cache);
                                        appendToTable($this[0], cache_sorted);
                                }, 1);
                                return false;
                            }
                        });
                    });
                }
                
                this.addParser = function (parser) {
                    var l = parsers.length,
                        a = true;
                    for (var i = 0; i < l; i++) {
                        if (parsers[i].id.toLowerCase() == parser.id.toLowerCase()) {
                            a = false;
                        }
                    }
                    if (a) {
                        parsers.push(parser);
                    };
                };
                this.formatFloat = function (s) {
                    var i = parseFloat(s);
                    return (isNaN(i)) ? 0 : i;
                };
                this.formatInt = function (s) {
                    var i = parseInt(s);
                    return (isNaN(i)) ? 0 : i;
                };
                this.isDigit = function (s, config) {
                    // replace all an wanted chars and match.
                    return /^[-+]?\d*$/.test($.trim(s.replace(/[,.']/g, '')));
                };
                
                function appendToTable(table, cache) {
                    var c = cache,
                        r = c.row,
                        n = c.normalized,
                        totalRows = n.length,
                        checkCell = (n[0].length - 1),
                        rows = [],
                        $t = $('ol');
                        
                      for (var i = 0; i < totalRows; i++) { 
                            var pos = n[i][checkCell];
                            $t.append(r[pos][0]);
                      }                 
                }
                  
                function multisort(table, sortList, cache) {
                    //console.log(cache.normalized);
                    var dynamicExp = "var sortWrapper = function(a,b) {",
                        l = sortList.length;
                    for (var i = 0; i < l; i++) {
                        var c = sortList[i][0];
                        var order = sortList[i][1];
                        //console.log(config.parsers[c].type);
                        var s = (table.config.parsers[c].type == "text") ? ((order == 0) ? makeSortFunction("text", "asc", c) : makeSortFunction("text", "desc", c)) : ((order == 0) ? makeSortFunction("numeric", "asc", c) : makeSortFunction("numeric", "desc", c));
                        var e = "e" + i;
                        dynamicExp += "var " + e + " = " + s;
                        dynamicExp += "if(" + e + ") { return " + e + "; } ";
                        dynamicExp += "else { ";
                    }
                    // if value is the same keep orignal order
                    var orgOrderCol = cache.normalized[0].length - 1;
                    dynamicExp += "return a[" + orgOrderCol + "]-b[" + orgOrderCol + "];";
                    for (var i = 0; i < l; i++) {
                        dynamicExp += "}; ";
                    }
                    dynamicExp += "return 0; ";
                    dynamicExp += "}; ";
                    
                    eval(dynamicExp);
                    cache.normalized.sort(sortWrapper);
                    return cache;
                }
                
                function makeSortFunction(type, direction, index) {
                    var a = "a[" + index + "]",
                        b = "b[" + index + "]";
                    if (type == 'text' && direction == 'asc') {
                        return "(" + a + " == " + b + " ? 0 : (" + a + " === null ? Number.POSITIVE_INFINITY : (" + b + " === null ? Number.NEGATIVE_INFINITY : (" + a + " < " + b + ") ? -1 : 1 )));";
                    } else if (type == 'text' && direction == 'desc') {
                        return "(" + a + " == " + b + " ? 0 : (" + a + " === null ? Number.POSITIVE_INFINITY : (" + b + " === null ? Number.NEGATIVE_INFINITY : (" + b + " < " + a + ") ? -1 : 1 )));";
                    } else if (type == 'numeric' && direction == 'asc') {
                        return "(" + a + " === null && " + b + " === null) ? 0 :(" + a + " === null ? Number.POSITIVE_INFINITY : (" + b + " === null ? Number.NEGATIVE_INFINITY : " + a + " - " + b + "));";
                    } else if (type == 'numeric' && direction == 'desc') {
                        return "(" + a + " === null && " + b + " === null) ? 0 :(" + a + " === null ? Number.POSITIVE_INFINITY : (" + b + " === null ? Number.NEGATIVE_INFINITY : " + b + " - " + a + "));";
                    }
                };
                
                function buildCache(table) {
                    var totalRows = (table.childElementCount) || 0,
                        totalCells = table.children[0].children.length - 1 || 0,  // one among them is <br>
                        cache = {
                            row: [],
                            normalized: []
                        },
                        data;  
                    for (var i = 0; i < totalRows; ++i) {
                        var c = $(table.children[i]),
                            cols = [];
                        cache.row.push(c);
                        for (var j = 0; j < totalCells; ++j) {
                            var ref_cell =  table.children[i].children[j];
                            if (ref_cell.childNodes.length > 1){  //version (one div is hidden)
                                data = ref_cell.children[0].innerHTML; 
                                cols.push(parsers[j].format(data, table));  
                            }else{
                                data = ref_cell.innerHTML;
                                cols.push(parsers[j].format(data, table));
                            }
                        }
                        cols.push(cache.normalized.length);
                        cache.normalized.push(cols);
                        cols = null;
                    }
                    return cache;
                }
                           
                function buildParserCache(table){
                    if (table.childElementCount == 0) return; // In the case of empty tables
                    var rows = table.children;
                    if (rows[0]) {
                        var list = [],
                        cells = rows[0].children;             
                        for (var item, i = -1; item = cells[++i];) {
                            if (item.nodeName != 'BR') {     
                                p = detectParserForColumn(table, rows, -1, i);
                                list.push(p);
                            }
                        };  
                    };
                    return list;
                };
                
                function detectParserForColumn(table, rows, rowIndex, cellIndex) {
                    var len = parsers.length,
                    node = false,
                    nodeValue = false,
                    keepLooking = true;
                    
                    while (nodeValue == '' && keepLooking) {
                        rowIndex++;
                        if (rows[rowIndex]) {
                            node = rows[rowIndex].children[cellIndex];
                            if (node.childNodes.length > 1){     //the columns like Version, where we'll have hidden div   
                                nodeValue = node.children[0].innerHTML;
                            }else {
                                nodeValue = node.innerHTML;
                            }     
                        } else {
                            keepLooking = false;
                        } 
                    }
                    for (var i = 1; i < len; i++) {
                        if (parsers[i].is(nodeValue, table, node)) {  
                            t = 1;
                            return parsers[i];
                        }
                    }
                    // default parser type: "text"
                    return parsers[0];
                }
            }
        });
              
        $.fn.extend({
            listsorter: $.listsorter.construct
        });
        
        // make shortcut
        var ls = $.listsorter;
        
        // add default parsers
        ls.addParser({
            id: "text",
            is: function (s) {
                return true;
            }, format: function (s) {
                return $.trim(s.toLocaleLowerCase());
            }, type: "text"
        });
        
        ls.addParser({
            id: "digit",
            is: function (s, table) {
                var c = table.config;
                return $.listsorter.isDigit(s, c);
            }, format: function (s) {
                return $.listsorter.formatFloat(s);
            }, type: "numeric"
        });
        
        ls.addParser({
            id: "currency",
            is: function (s) {
                return /^[£$€?.]/.test(s);
            }, format: function (s) {
                return $.listsorter.formatFloat(s.replace(new RegExp(/[£$€]/g), ""));
            }, type: "numeric"
        });

        ls.addParser({
            id: "ipAddress",
            is: function (s) {
                return /^\d{2,3}[\.]\d{2,3}[\.]\d{2,3}[\.]\d{2,3}$/.test(s);
            }, format: function (s) {
                var a = s.split("."),
                    r = "",
                    l = a.length;
                for (var i = 0; i < l; i++) {
                    var item = a[i];
                    if (item.length == 2) {
                        r += "0" + item;
                    } else {
                        r += item;
                    }
                }
                return $.listsorter.formatFloat(r);
            }, type: "numeric"
        });
        
        ls.addParser({
            id: "url",
            is: function (s) {
                return /^(https?|ftp|file):\/\/$/.test(s);
            }, format: function (s) {
                return jQuery.trim(s.replace(new RegExp(/(https?|ftp|file):\/\//), ''));
            }, type: "text"
        });

        ls.addParser({
            id: "isoDate",
            is: function (s) {
                return /^\d{4}[\/-]\d{1,2}[\/-]\d{1,2}$/.test(s);
            }, format: function (s) {
                return $.listsorter.formatFloat((s != "") ? new Date(s.replace(
                new RegExp(/-/g), "/")).getTime() : "0");
            }, type: "numeric"
        });

        ls.addParser({
            id: "percent",
            is: function (s) {
                return /\%$/.test($.trim(s));
            }, format: function (s) {
                return $.listsorter.formatFloat(s.replace(new RegExp(/%/g), ""));
            }, type: "numeric"
        });

        ls.addParser({
            id: "usLongDate",
            is: function (s) {
                return s.match(new RegExp(/^[A-Za-z]{3,10}\.? [0-9]{1,2}, ([0-9]{4}|'?[0-9]{2}) (([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(AM|PM)))$/));
            }, format: function (s) {
                return $.listsorter.formatFloat(new Date(s).getTime());
            }, type: "numeric"
        });

        ls.addParser({
            id: "shortDate",
            is: function (s) {
                return /\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/.test(s);
            }, format: function (s, table) {
                var c = table.config;
                s = s.replace(/\-/g, "/");
                if (c.dateFormat == "us") {
                    // reformat the string in ISO format
                    s = s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/, "$3/$1/$2");
                } else if (c.dateFormat == "uk") {
                    // reformat the string in ISO format
                    s = s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/, "$3/$2/$1");
                } else if (c.dateFormat == "dd/mm/yy" || c.dateFormat == "dd-mm-yy") {
                    s = s.replace(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})/, "$1/$2/$3");
                }
                return $.listsorter.formatFloat(new Date(s).getTime());
            }, type: "numeric"
        });
    
        ls.addParser({
            id: "time",
            is: function (s) {
                return /^(([0-2]?[0-9]:[0-5][0-9])|([0-1]?[0-9]:[0-5][0-9]\s(am|pm)))$/.test(s);
            }, format: function (s) {
                return $.listsorter.formatFloat(new Date("2000/01/01 " + s).getTime());
            }, type: "numeric"
        });
        
       
        ls.addParser({
            id: "metadata",
            is: function (s) {
                return false;
            }, format: function (s, table, cell) {
                var c = table.config,
                    p = (!c.parserMetadataName) ? 'sortValue' : c.parserMetadataName;
                //return $(cell).metadata()[p];
                $.trim(s.toLocaleLowerCase());
            }, type: "text"
        });
        
})(jQuery);