"""
Define the base classes for the Sumatra version control abstraction layer.
"""

import os.path

class Repository(object):
    
    def __init__(self, url):
        if url == ".":
            url = os.path.abspath(url)
        self.url = url
        
    def __str__(self):
        return "%s at %s" % (self.__class__.__name__, self.url)
        

class WorkingCopy(object):
    pass


