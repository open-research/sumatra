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
    
    def in_stdlib(self, executable_path):
        stdlib_path = _nrn_install_prefix(executable_path)
        return self.path.find(stdlib_path) == 0

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
    return set(all_paths)


def _nrn_install_prefix(executable_path):
    """
    Determine the install location based on the executable path. Can think of
    lots of ways this could go wrong.
    """
    executable_dir = os.path.dirname(executable_path)
    return os.path.realpath(os.path.join(executable_dir, "../.."))


def find_loaded_files(file_path, executable_path):
    """
    Find all files that are loaded with load_file(), whether directly or
    indirectly, by a given Hoc file. Note that this only handles cases whether
    the path is given directly, not where it has been previously assigned to a
    strdef. Also note that this is more complicated than xopen(), since NEURON
    also looks in any directories in $HOC_LIBRARY_PATH and $NEURONHOME/lib/hoc.
    """
    op = os.path
    search_dirs = []
    if "HOC_LIBRARY_PATH" in os.environ:
        search_dirs.extend(os.environ["HOC_LIBRARY_PATH".split(":")]) # could also be space-separated
    if "NEURONHOME" in os.environ:
        search_dirs.append(os.environ["NEURONHOME"])
    else:
        prefix = _nrn_install_prefix(executable_path)
        search_dirs.append(op.join(prefix, "share/nrn/lib/hoc"))
    print "SEARCH_DIRS", search_dirs
    load_file_pattern = re.compile(r'load_file\("(?P<path>[\w\.\/]+)"\)')
    all_paths = []
    def find_file(path, current_directory):
        """
        Look for path as an absolute path then relative to the current directory,
        then relative to search_dirs.
        Return the absolute path.
        """
        if op.exists(path):
            return op.abspath(path)
        for dir in [current_directory] + search_dirs:
            search_path = op.join(dir, path)
            if op.exists(search_path):
                return search_path
        raise Exception("File %s does not exist" % path)
    def find(start_path, paths):
        """
        Recursively look for files loaded by start_path, add them to paths.
        """
        with open(start_path) as f:
            new_paths = load_file_pattern.findall(f.read())
        curdir = op.dirname(start_path)
        new_paths = [find_file(p, curdir) for p in new_paths]
        #if new_paths:
        #    print start_path, "loads the following:\n ", "\n  ".join(new_paths)
        #else:
        #    print start_path, "loads no files"
        paths.extend(new_paths)
        for path in new_paths:
            find(path, paths)
    find(file_path, all_paths)
    return set(all_paths)


def find_dependencies(filename, on_changed, executable_path):
    """Return a list of Dependency objects representing all Hoc files imported
    (directly or indirectly) by a given Hoc file."""
    paths = find_xopened_files(filename).union(find_loaded_files(filename, executable_path))
    dependencies = [Dependency(name, on_changed=on_changed) for name in paths]
    return [d for d in dependencies if not d.in_stdlib(executable_path)]