

class Repository(object):
    
    def __init__(self, url):
        self.url = url
        
    def __str__(self):
        return "%s at %s" % (self.__class__.__name__, self.url)
        

class WorkingCopy(object):
    pass


