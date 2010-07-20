"""
Functions for finding the version of a dependency.

Classes
-------
BaseDependency - base class for holding information about a program component.

Functions
---------

find_version_from_versioncontrol - determines whether a file is under version
                                   control, and if so, obtains version
                                   information from this.

find_version()                   - tries to find version information by calling a
                                   series of functions in turn.

"""

import os
from sumatra import versioncontrol

def find_version_from_versioncontrol(path):
    """Determine whether a file is under version control, and if so,
       obtain version information from this."""
    #print "Looking for working copy at %s" % path
    try:
        wc = versioncontrol.get_working_copy(path)
    except versioncontrol.VersionControlError:
        version = 'unknown'
    else:
        if wc.has_changed():
            msg = "Working copy at %s has uncommitted modifications. It is therefore not possible to determine the code version. Please commit your modifications." % path
            raise versioncontrol.UncommittedModificationsError(msg)
        version = wc.current_version()
    return version


# add support for using packaging systems, e.g. apt, to find versions.

# add support for looking for Subversion $Id:$ tags, etc.


def find_version(component, heuristics):
    """
    Try to find version information by calling a series of functions in turn.
    
    `component` - type depends on the language, e.g. a module for Python, a
                  filesystem path for NEURON.
    `heuristics` - a list of functions that accept a component as the single
                   argument and return a version number or 'unknown'.
    """
    errors = []
    for heuristic in heuristics:
        version = heuristic(component)
        if version is not 'unknown':
            break
    return str(version)


def find_file(path, current_directory, search_dirs):
    """
    Look for path as an absolute path then relative to the current directory,
    then relative to search_dirs.
    Return the absolute path.
    """
    op = os.path
    if op.exists(path):
        return op.abspath(path)
    for dir in [current_directory] + search_dirs:
        search_path = op.join(dir, path)
        if op.exists(search_path):
            return search_path
    raise Exception("File %s does not exist" % path)



class BaseDependency(object):
    """
    Contains information about a program component, and tries to determine version information.
    """
    
    def __init__(self, name, path=None, version=None, on_changed='error'):
        pass
        
    def __repr__(self):
        return "%s (%s) version=%s%s" % (self.name, self.path, self.version, self.diff and "*" or '')
        
    def __eq__(self, other):
        return self.name == other.name and self.path == other.path and \
               self.version == other.version and self.diff == other.diff
        
    def __ne__(self, other):
        return not self.__eq__(other)

