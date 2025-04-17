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


:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import os
from sumatra import versioncontrol


def find_versions_from_versioncontrol(dependencies):
    """Determine whether a file is under version control, and if so,
       obtain version information from this."""
    for dependency in dependencies:
        if dependency.version == "unknown":
            try:
                wc = versioncontrol.get_working_copy(dependency.path)
            except versioncontrol.VersionControlError:
                pass  # dependency.version remains "unknown"
            else:
                if wc.has_changed():
                    dependency.diff = wc.diff()
                dependency.version = wc.current_version()
                dependency.source = wc.repository.url
    return dependencies


# add support for using packaging systems, e.g. apt, to find versions.

# add support for looking for Subversion $Id:$ tags, etc.


def find_versions(dependencies, heuristics):
    """
    Try to find version information by calling a series of functions in turn.

    *dependencies*:
        a list of Dependency objects.
    *heuristics*:
        a list of functions that accept a component as the single
        argument and return a version number or 'unknown'.

    Returns a possibly modified list of dependencies
    """
    for heuristic in heuristics:
        dependencies = heuristic(dependencies)
    return dependencies


def find_file(path, current_directory, search_dirs):
    """
    Look for path as an absolute path then relative to the current directory,
    then relative to *search_dirs*.
    Return the absolute path.
    """
    op = os.path
    if op.exists(path):
        return op.abspath(path)
    for dir in [current_directory] + search_dirs:
        search_path = op.join(dir, path)
        if op.exists(search_path):
            return search_path
    raise IOError("File %s does not exist" % path)


class BaseDependency(object):

    """
    Contains information about a program component, and tries to determine version information.

    *name*:
        an identifying name, e.g. the module name in Python
    *path*:
        the location of the dependency file in the local filesystem
    *version*:
        the version of the dependency, if that can be determined, otherwise
        'unknown'. Always a string, even if the version can also be represented
        as a number.
    *diff*:
        if the dependency is under version control and has been modified, the
        diff between the actual version and the last-committed version.
    *source*:
        an identifier for where the dependency came from, if known, e.g. the
        url of a version control repository or the name of a Linux package.

    """

    def __init__(self, name, path=None, version='unknown', diff='', source=None):
        self.name = name
        self.path = path
        self.diff = diff
        self.version = version
        self.source = source  # e.g. url of (upstream?) repository

    def __repr__(self):
        return "%s (%s) version=%s%s" % (self.name, self.path, self.version, self.diff and "*" or '')

    def __eq__(self, other):
        return self.name == other.name and self.path == other.path and \
            self.version == other.version and self.diff == other.diff

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name) ^ hash(self.path) ^ hash(self.version) ^ hash(self.diff)
