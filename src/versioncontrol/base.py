"""
Define the base classes for the Sumatra version control abstraction layer.
"""

import os.path


class VersionControlError(Exception):
    pass


class Repository(object):
    
    def __init__(self, url, upstream=None):
        if url == ".":
            url = os.path.abspath(url)
        self.url = url
        self.upstream = upstream
        
    def __str__(self):
        s = "%s at %s" % (self.__class__.__name__, self.url)
        if self.upstream:
            s += " (upstream: %s)" % self.upstream
        return s
    
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.url == other.url
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'upstream': self.upstream}

    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.upstream = state['upstream']


class WorkingCopy(object):
    
    def __eq__(self, other):
        return (self.repository == other.repository) and (self.path == other.path) \
               and (self.current_version() == other.current_version()) #and (self.diff() == other.diff())
            
    def __ne__(self, other):
        return not self.__eq__(other)

    def contains(self, path):
        """
        Does the repository contain the file with the given path?
        
        where `path` is relative to the working copy root.
        """
        status = self.status()    
        return (path in status['modified']) or (path in status['clean'])
