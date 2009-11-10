"""
The dependency_finder module attempts to determine all the dependencies of a
given simulation script, including the version of each dependency.

It is currently rather Python-specific, but other simulation languages that
support some method of importing or including other files, e.g. Hoc, will also
be supported.

Classes
-------
Dependency - contains information about a Python module or package, and tries
             to determine version information.

Functions
---------

find_version_by_attribute() - tries to find version information from the
                              attributes of a Python module.
find_version_from_egg()     - determines whether a Python module is provided as
                              an egg, and if so, obtains version information
                              from this.
find_version_from_versioncontrol() - determines whether a Python module is
                                     under version control, and if so, obtains
                                     version information from this.
find_version()              - tries to find version information by calling a
                              series of functions in turn.
find_imported_packages()    - finds all imported top-level packages for a given
                              Python file.
find_dependencies_python()  - returns a list of Dependency objects representing
                              all the top-level modules or packages imported
                              (directly or indirectly) by a given Python file.
find_dependencies()         - returns a list of dependencies for a given script
                              and programming langauge. Currently only supports
                              Python.

Module variables
----------------

heuristics - a list of functions that will be called in sequence by
             find_version()
"""

from __future__ import with_statement
from types import ModuleType
from modulefinder import ModuleFinder
import imp
import distutils.sysconfig
import os
import sys
from sumatra import versioncontrol

stdlib_path = distutils.sysconfig.get_python_lib(standard_lib=True)


def find_version_by_attribute(module):
    """Try to find version information from the attributes of a Python module."""
    version = 'unknown'
    for attr_name in 'version', 'get_version', '__version__', 'VERSION':
        if hasattr(module, attr_name):
            attr = getattr(module, attr_name)
            if callable(attr):
                version = attr()
            elif isinstance(attr, ModuleType):
                version = find_version_by_attribute(attr)
            else:
                version = attr
            break
    if version is None: version = 'unknown'
    return version

def find_version_from_egg(module):
    """Determine whether a Python module is provided as an egg, and if so,
       obtain version information from this."""
    version = 'unknown'
    dir = os.path.dirname(module.__file__)
    if 'EGG-INFO' in os.listdir(dir):
        with open(os.path.join(dir, 'EGG-INFO', 'PKG-INFO')) as f:
            for line in f.readlines():
                if line[:7] == 'Version':
                    version = line.split(' ')[1].strip()
                    attr_name = 'egg-info'
                    break
    return version

def find_version_from_versioncontrol(module):
    """Determine whether a Python module is under version control, and if so,
       obtain version information from this."""
    #print "Looking for working copy at %s" % module.__path__[0]
    try:
        wc = versioncontrol.get_working_copy(module.__path__[0])
    except versioncontrol.VersionControlError:
        version = 'unknown'
    else:
        #print "Found working copy for %s" % module.__name__
        if wc.has_changed():
            msg = "Working copy at %s has uncommitted modifications. It is therefore not possible to determine the code version. Please commit your modifications." % module.__path__[0]
            raise versioncontrol.UncommittedModificationsError(msg)
        version = wc.current_version()
    return version
    

heuristics = [find_version_from_versioncontrol,
              find_version_by_attribute,
              find_version_from_egg]

def find_version(module, extra_heuristics=[]):
    """Try to find version information by calling a series of functions in turn."""
    heuristics.extend(extra_heuristics)
    errors = []
    for heuristic in heuristics:
        version = heuristic(module)
        if version is not 'unknown':
            break
    return str(version)
    
    # Other possible heuristics:
    #   * check for an egg-info file with a similar name to the module
    #     although this is not really safe, as there can be old egg-info files
    #     lying around.
    #   * could also look in the __init__.py for a Subversion $Id:$ tag

def find_imported_packages(filename):
    """Find all imported top-level packages for a given Python file."""
    # if using a different Python as the simulator from the one used to run Sumatra,
    # there is a strong risk that different packages will be found. This is a major bug.
    finder = ModuleFinder(path=sys.path[1:], debug=2)
    # note that we remove the first element of sys.path to stop modules in the
    # sumatra source directory with the same name as standard library modules,
    # e.g. "commands", being loaded when the standard library module was wanted.
    finder_output = open("module_finder_output.txt", "w")
    sys.stdout = finder_output
    finder.run_script(os.path.abspath(filename))
    sys.stdout = sys.__stdout__
    finder_output.close()
    top_level_packages = {}
    for name, module in finder.modules.items():
        if module.__path__ and "." not in name:
            top_level_packages[name] = module
    return top_level_packages


class Dependency(object):
    """
    Contains information about a Python module or package, and tries to
    determine version information.
    """
    
    def __init__(self, module_name, path=None, version=None, on_changed='error'):
        self.name = module_name
        if path:
            self.path = path
        else:
            file_obj, self.path, description = imp.find_module(self.name)
        self.in_stdlib = os.path.dirname(self.path) == stdlib_path
        self.diff = ''
        if version:
            self.version = version
        else:
            m = self._import()
            if m:
                try:
                    self.version = find_version(m)
                except versioncontrol.UncommittedModificationsError:
                    if on_changed == 'error':
                        raise
                    elif on_changed == 'store-diff':
                        wc = versioncontrol.get_working_copy(m.__path__[0])
                        self.version = wc.current_version()
                        self.diff = wc.diff()
                    else:
                        raise Exception("Only 'error' and 'store-diff' are currently supported for on_changed.")
            else:
                self.version = 'unknown'
        
    def __repr__(self):
        return "%s (%s) version=%s%s" % (self.name, self.path, self.version, "*" and self.diff or '')
    
    def _import(self):
        self.import_error = None
        try:
            m = __import__(self.name)
        except ImportError, e:
            self.import_error = e
            m = None
        return m
        
        
def find_dependencies_python(filename, on_changed):
    """Return a list of Dependency objects representing all the top-level
       modules or packages imported (directly or indirectly) by a given Python file."""
    packages = find_imported_packages(filename)
    dependencies = [Dependency(name, on_changed=on_changed) for name in packages]
    return [d for d in dependencies if not d.in_stdlib]

def find_dependencies(filename, executable, on_changed='error'):
    """Return a list of dependencies for a given script and programming
       language. Currently only supports Python."""
    if executable.name == "Python":
        return find_dependencies_python(filename, on_changed)
    else:
        raise Exception("find_dependencies() not yet implemented for %s" % executable.name)


def test():
    for file in os.listdir(distutils.sysconfig.get_python_lib()):
        ext = os.path.splitext(file)[1]
        if ext == '' or ext == '.egg':
            file = file.split('-')[0]
            try:
                m = __import__(file)
                print file, find_version(m)
            except ImportError:
                pass

        
if __name__ == "__main__":
    import sys
    import programs
    print "\n".join(str(d) for d in find_dependencies(sys.argv[1],
                                                      programs.PythonExecutable(None)))
