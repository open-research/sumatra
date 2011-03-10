"""
GENESIS-specific functions for finding information about dependencies.

Classes
-------
Dependency - contains information about a .g or .p file, and tries to determine
             version information.

Functions
---------

find_version_from_versioncontrol() - determines whether a GENESIS file is
                                     under version control, and if so, obtains
                                     version information from this.
find_included_files()              - finds all included .g files for a given GENESIS file.
find_dependencies()                - returns a list of Dependency objects representing
                                     all the  files imported by a given GENESIS file.

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
import subprocess

heuristics = [core.find_version_from_versioncontrol,]

class Dependency(core.BaseDependency):
    """
    Contains information about a Hoc file, and tries to determine version information.
    """
    module = 'genesis'
    
    def __init__(self, name, path=None, version=None, on_changed='error'):
        self.name = os.path.basename(name) # or maybe should be path relative to main file?
        if path:
            self.path = path
        else:
            self.path = os.path.abspath(name)
        if not os.path.exists(self.path):
            raise IOError("File %s does not exist." % self.path)
        self.diff = ''
        if version:
            self.version = version
        else:
            self.version = "unknown"
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


def get_sim_path():
    """
    Obtain the SIMPATH by parsing ~/.simrc
    """
    # this is rather hacky, to say the least
    with open(os.path.expanduser("~/.simrc")) as fd:
        content = fd.read().replace("\\\n", "")
    lines = [line[15:] for line in content.split("\n") if "setenv SIMPATH" in line]
    if len(lines) > 1:
        for i in range(1, len(lines)):
            lines[i] = lines[i].replace("{getenv SIMPATH}", lines[0])
    return lines[-1].split()
    

def find_included_files(file_path):
    """
    Find all files that are included, whether directly or indirectly, by a given
    .g file. 
    """
    comment_pattern = re.compile('/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/') # see http://ostermiller.org/findcomment.html
    include_pattern = re.compile(r'include (?P<path>[\w\./]+)')
    search_dirs = get_sim_path()
    all_paths = []    
    def find(start_path, paths):
        """
        Recursively look for files loaded by start_path, add them to paths.
        """
        with open(start_path) as f:
            without_comments = comment_pattern.sub("", f.read())
        new_paths = include_pattern.findall(without_comments)
        def add_ext(path):
            if path[-2:] != ".g":
                path += ".g"
            return path
        new_paths = (add_ext(p) for p in new_paths)
        curdir = os.path.dirname(start_path)
        new_paths = [core.find_file(p, curdir, search_dirs) for p in new_paths]
        if new_paths:
            print start_path, "loads the following:\n ", "\n  ".join(new_paths)
        else:
            print start_path, "loads no files"
        paths.extend(new_paths)
        for path in new_paths:
            find(path, paths)
    find(file_path, all_paths)
    return set(all_paths)



def find_dependencies(filename, executable_path, on_changed):
    """Return a list of Dependency objects representing all Hoc files imported
    (directly or indirectly) by a given Hoc file."""
    paths = find_included_files(filename)
    # also need to find .p files
    dependencies = [Dependency(name, on_changed=on_changed) for name in paths]
    return dependencies