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


:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import re
import os
from sumatra.dependency_finder import core


class Dependency(core.BaseDependency):
    """
    Contains information about a Hoc file, and tries to determine version information.
    """
    module = 'neuron'

    def __init__(self, name, path=None, version='unknown', diff='', source=None):
        super(Dependency, self).__init__(os.path.basename(name),
                                         path or os.path.abspath(name),
                                         version, diff, source)

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
        # print "-", path, new_paths
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
    executable_dir = os.path.dirname(os.path.realpath(executable_path))
    return os.path.join(executable_dir, "../..")


def find_loaded_files(file_path, executable_path):
    """
    Find all files that are loaded with :func:`load_file()`, whether directly or
    indirectly, by a given Hoc file. Note that this only handles cases whether
    the path is given directly, not where it has been previously assigned to a
    strdef. Also note that this is more complicated than :func:`xopen()`, since
    NEURON also looks in any directories in ``$HOC_LIBRARY_PATH`` and
    ``$NEURONHOME/lib/hoc``.
    """
    op = os.path
    search_dirs = []
    if "HOC_LIBRARY_PATH" in os.environ:
        search_dirs.extend(os.environ["HOC_LIBRARY_PATH".split(":")])  # could also be space-separated
    if "NEURONHOME" in os.environ:
        search_dirs.append(os.environ["NEURONHOME"])
    else:
        prefix = _nrn_install_prefix(executable_path)
        search_dirs.append(op.join(prefix, "share/nrn/lib/hoc"))
    load_file_pattern = re.compile(r'load_file\("(?P<path>[\w\.\/]+)"\)')
    all_paths = []

    def find(start_path, paths):
        """
        Recursively look for files loaded by start_path, add them to paths.
        """
        with open(start_path) as f:
            new_paths = load_file_pattern.findall(f.read())
        curdir = op.dirname(start_path)
        new_paths = [core.find_file(p, curdir, search_dirs) for p in new_paths]
        # if new_paths:
        #    print start_path, "loads the following:\n ", "\n  ".join(new_paths)
        # else:
        #    print start_path, "loads no files"
        paths.extend(new_paths)
        for path in new_paths:
            find(path, paths)
    find(file_path, all_paths)
    return set(all_paths)


def find_dependencies(filename, executable):
    """Return a list of Dependency objects representing all Hoc files imported
    (directly or indirectly) by a given Hoc file."""
    executable_path = os.path.realpath(executable.path)
    heuristics = [core.find_versions_from_versioncontrol, ]
    paths = find_xopened_files(filename).union(find_loaded_files(filename, executable.path))
    dependencies = [Dependency(name) for name in paths]
    dependencies = [d for d in dependencies if not d.in_stdlib(executable.path)]
    return core.find_versions(dependencies, heuristics)
