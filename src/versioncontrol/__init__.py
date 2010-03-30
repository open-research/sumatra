"""
The versioncontrol sub-package provides an abstraction layer around different
revision/version control systems. Only the functionality required for recording
version numbers and switching the working copy between different versions is
wrapped - for more complex tasks such as merging, branching, etc., the
version control tool should be used directly.

Sub-modules
-----------

base        - defines the base WorkingCopy and Repository classes
_mercurial  - defines MercurialWorkingCopy and MercurialRepository classes
_subversion - defines SubversionWorkingCopy and SubversionRepository classes

Exceptions
----------

VersionControlError - generic Exception class for problems with version control

Functions
---------

get_working_copy() - given a filesystem path, determine if a working copy exists
                     and return an appropriate WorkingCopy object if so.
get_repository()   - determine whether a revision control system repository
                     exists at a given URL and return an appropriate Repository
                     object if so.
"""

import sys
import os

from base import VersionControlError

class UncommittedModificationsError(Exception):
    pass

vcs_list = []

for vcs in ['mercurial', 'subversion']:
    try:
        __import__('sumatra.versioncontrol._%s' % vcs)
        vcs_list.append(sys.modules['sumatra.versioncontrol._%s' % vcs])
    except ImportError:
        pass
    
if len(vcs_list) == 0:
    raise VersionControlError("No version control systems found.")
        
def get_working_copy(path=None):
    path = path or os.getcwd()
    for vcs in vcs_list:
        if vcs.may_have_working_copy(path):
            return vcs.get_working_copy(path)
    raise VersionControlError("No working copy found") # add some diagnostic information
            
def get_repository(url):
    if url:
        repos = None
        for vcs in vcs_list:
            try:
                repos =  vcs.get_repository(url)
                break
            except Exception, e:
                print e
        if repos is None:
            raise Exception("Can't find repository at URL '%s'" % url)
        else:
            return repos
    else:
        working_copy = get_working_copy()
        if working_copy:
            return working_copy.repository
        else:
            return None