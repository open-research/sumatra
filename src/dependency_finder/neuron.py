"""
NEURON-specific functions for finding information about dependencies.

Classes
-------
Dependency - contains information about a Hoc file, and tries to determine
             version information. In the future, will also handle NMODL files.

Functions
---------

find_version_from_versioncontrol() - determines whether a Hoc file is
                                     under version control, and if so, obtains
                                     version information from this.
find_xopened_files()        - finds all xopened Hoc files for a given Hoc file.
find_dependencies()         - returns a list of Dependency objects representing
                              all the Hoc files imported by a given Hoc file. In
                              the future should also return NMODL dependencies.

Module variables
----------------

heuristics - a list of functions that will be called in sequence by
             find_version()
"""

from __future__ import with_statement
import re
import os
from sumatra.dependency_finder import core
from sumatra import versioncontrol

heuristics = [core.find_version_from_versioncontrol,]

class Dependency(core.BaseDependency):
    """
    Contains information about a Hoc file, and tries to determine version information.
    """
    module = 'neuron'
    
    def __init__(self, name, path=None, version=None, on_changed='error'):
        self.name = name
        if path:
            self.path = path
        else:
            self.path = os.path.abspath(name)
        self.diff = ''
        if version:
            self.version = version
        else:
            try:
                self.version = core.find_version(self.path, heuristics)
            except versioncontrol.UncommittedModificationsError:
                if on_changed == 'error':
                    raise
                elif on_changed == 'store-diff':
                    wc = versioncontrol.get_working_copy(self.path)
                    self.version = wc.current_version()
                    self.diff = wc.diff()
                else:
                    raise Exception("Only 'error' and 'store-diff' are currently supported for on_changed.")
            else:
                self.version = 'unknown'


def find_xopened_files(file_path):
    """
    Find all files that are xopened, whether directly or indirectly, by a given
    Hoc file. Note that this only handles cases whether the path is given
    directly, not where it has been previously assigned to a strdef.
    """
    xopen_pattern = re.compile(r'xopen\("(?P<path>\w+\.*\w*)"\)')
    all_paths = []
    def find(path, paths):
        current_dir = os.path.dirname(path)
        with open(path) as f:
            new_paths = xopen_pattern.findall(f.read())
        #print "-", path, new_paths
        new_paths = [os.path.join(current_dir, path) for path in new_paths]
        paths.extend(new_paths)
        for path in new_paths:
            find(path, paths)
    find(os.path.abspath(file_path), all_paths)
    return all_paths

def find_dependencies(filename, on_changed):
    """Return a list of Dependency objects representing all Hoc files imported
    (directly or indirectly) by a given Hoc file."""
    files_xopened = find_xopened_files(filename)
    dependencies = [Dependency(name, on_changed=on_changed) for name in files_xopened]
    return dependencies