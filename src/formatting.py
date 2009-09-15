import textwrap

fields = ['label', 'reason', 'outcome', 'duration', 'script',
          'executable', 'timestamp']

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
                else:
                    entryStr += str(entry)
                output += textwrap.fill(entryStr, width=text_width,
                                        replace_whitespace=False,
                                        subsequent_indent=' '*(indent+2)) + "\n"
        return output
    
    
class HTMLFormatter(Formatter):
    
    def short(self):
        raise NotImplementedError
    
    
formatters = {
    'text': TextFormatter,
    'html': HTMLFormatter,
}
        
def get_formatter(format):
    return formatters[format]