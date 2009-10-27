"""
The formatting module provides classes for formatting simulation records in
different ways: summary, list or table; and in different mark-up formats:
currently text or HTML.

Classes
-------

TextFormatter - formats records as text
HTMLFormatter - formats records as HTML

Function
--------

get_formatter() - return an approriate Formatter object for a given requested
                  format.
"""

import textwrap

fields = ['label', 'reason', 'outcome', 'duration', 'repository', 'main_file',
          'version', 'executable', 'timestamp', 'tags']

class Formatter(object):
    
    def __init__(self, records):
        self.records = records
        
    def format(self, mode='short'):
        return getattr(self, mode)()


class TextFormatter(Formatter):
    
    def short(self):
        return "\n".join(record.label for record in self.records)
            
    def long(self):
        text_width = 80; indent = 13
        output = ""
        for record in self.records:
            output += "-" * text_width + "\n"
            for field in fields:
                entryStr = "%s%d%s" % ("%-",indent,"s: ") % field.title()
                entry = getattr(record,field)
                if callable(entry):
                    entryStr += str(entry())
                elif hasattr(entry, "items"):
                    entryStr += ", ".join(["%s=%s" % item for item in entry.items()])
                elif isinstance(entry, set):
                    entryStr += ", ".join(entry)
                else:
                    entryStr += str(entry)
                output += textwrap.fill(entryStr, width=text_width,
                                        replace_whitespace=False,
                                        subsequent_indent=' '*(indent+2)) + "\n"
        return output
    
    def table(self):
        raise NotImplementedError
    
class HTMLFormatter(Formatter):
    
    def short(self):
        raise NotImplementedError
    
    
formatters = {
    'text': TextFormatter,
    'html': HTMLFormatter,
}
        
def get_formatter(format):
    return formatters[format]