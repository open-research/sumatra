"""
Python-specific functions for finding information about dependencies.

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
find_imported_packages()    - finds all imported top-level packages for a given
                              Python file.
find_dependencies()         - returns a list of Dependency objects representing
                              all the top-level modules or packages imported
                              (directly or indirectly) by a given Python file.

Module variables
----------------

heuristics - a list of functions that will be called in sequence by
             find_version()
"""

from __future__ import with_statement
import os
import sys

from modulefinder import Module
import warnings
import inspect

from sumatra.dependency_finder import core
from sumatra import versioncontrol

SENTINEL = "<SUMATRA>"


def run_script(executable_path, script):
    """
    Execute a script provided as a multi-line string using the given executable,
    and evaluate the script stdout.
    """
    # if sys.executable == executable_path, we can just eval it and save the
    # process-creation overhead.
    import textwrap
    import subprocess
    script = str(script) # get problems if script is is unicode
    p = subprocess.Popen(executable_path, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output,err = p.communicate(textwrap.dedent(script)) # should handle err
    output = output[output.find(SENTINEL)+len(SENTINEL):]
    try:
        return_value = eval(output)
    except SyntaxError, errmsg:
        warnings.warn("Error in evaluating script output\n. Executable: %s\nScript: %s\nOutput: '%s'\nError: %s" % (executable_path, script, output, err))
        return_value = {}
    return return_value


def find_version_by_attribute(module):
    from types import ModuleType
    version = 'unknown'
    for attr_name in 'version', 'get_version', '__version__', 'VERSION':
        if hasattr(module, attr_name):
            attr = getattr(module, attr_name)
            if callable(attr):
                try:
                    version = attr()
                except TypeError:
                    continue
            elif isinstance(attr, ModuleType):
                version = find_version_by_attribute(attr)
            else:
                version = attr
            break
    if isinstance(version, tuple):
        version = ".".join(str(c) for c in version)
    return version


find_versions_by_attribute_template = """
import sys
%(def_find_version_by_attribute)s
module_names = %(module_names)s
versions = []
for name in module_names:
    try:
        module = __import__(name)
    except ImportError as err: # should do something with err
        module = None
    version = 'unknown'
    if module:
        version = find_version_by_attribute(module)
    versions.append(version)
sys.stdout.write("%(sentinel)s" + str(versions))
"""

def find_versions_by_attribute(dependencies, executable):
    """Try to find version information from the attributes of a Python module."""
    context = {
        'module_names': [d.name for d in dependencies if d.version == 'unknown'],
        'def_find_version_by_attribute': inspect.getsource(find_version_by_attribute),
        'sentinel': SENTINEL,
    }
    script = find_versions_by_attribute_template % context
    if executable.version[0] == '2':
        script = script.replace(' as', ',')  # Python 2.5 and earlier do not have the 'as' keyword
    versions = run_script(executable.path, script)
    i = 0
    for d in dependencies:
        if d.version == 'unknown':
            d.version = versions[i]
            i += 1
    return dependencies


def find_versions_from_egg(dependencies):
    """Determine whether a Python module is provided as an egg, and if so,
       obtain version information from this."""
    for dependency in dependencies:
        if dependency.version == 'unknown':
            dir = os.path.dirname(dependency.path) # should check if dirname ends in ".egg" - may need parent directory
            if os.path.isdir(dir):
                if 'EGG-INFO' in os.listdir(dir):
                    with open(os.path.join(dir, 'EGG-INFO', 'PKG-INFO')) as f:
                        for line in f.readlines():
                            if line[:7] == 'Version':
                                dependency.version = line.split(' ')[1].strip()
                                attr_name = 'egg-info'
                                break
    return dependencies


# Other possible heuristics:
#   * check for an egg-info file with a similar name to the module
#     although this is not really safe, as there can be old egg-info files
#     lying around.
#   * could also look in the __init__.py for a Subversion $Id:$ tag



class Dependency(core.BaseDependency):
    """
    Contains information about a Python module or package, and tries to
    determine version information.
    """
    module = 'python'

    def __init__(self, module_name, path, version='unknown', diff=''):
        self.name = module_name
        self.path = path
        self.diff = diff
        self.version = version

    @classmethod
    def from_module(cls, module, executable_path):
        """Create from modulefinder.Module instance."""
        path = os.path.realpath(module.__path__[0]) # resolve any symbolic links
        if len(module.__path__) > 1:
            raise Exception("This is not supposed to happen. Please tell the package developers about this.") # or I could figure out for myself when this could happen
        return cls(module.__name__, module.__path__[0])


def find_imported_packages(filename, executable_path, debug=0, exclude_stdlib=True):
    """
    Find all imported top-level packages for a given Python file.

    We cannot assume that the version of Python being used to run Sumatra is the
    same as that used to run the simulation/analysis. Therefore we need to run
    all the dependency finding and version checking in a subprocess with the
    correct version of Python.
    """
    #Actually, we could check whether executable_path matches sys.executable, and
    #then do it in this process. On the other hand, the dependency finding
    #could run in parallel with the simulation (good for multicore): we could
    #move setting of dependencies to after the simulation, rather than having it
    #in record.register()
    script = """
        from modulefinder import ModuleFinder
        import sys, os
        import distutils.sysconfig
        stdlib_path = distutils.sysconfig.get_python_lib(standard_lib=True)
        exclude_stdlib = %s
        finder = ModuleFinder(path=sys.path, debug=%d)
        finder.run_script("%s")
        top_level_packages = {}
        for name, module in finder.modules.items():
            if module.__path__ and "." not in name:
                if not(exclude_stdlib and os.path.dirname(module.__path__[0]) == stdlib_path): # doesn't work for platform-specific modules, e.g. 'Finder', 'Carbon'
                    top_level_packages[name] = module
        sys.stdout.write("%s" + str(top_level_packages))""" % (exclude_stdlib, int(debug), filename, SENTINEL)
    return run_script(executable_path, script)


def find_dependencies(filename, executable):
    """Return a list of Dependency objects representing all the top-level
       modules or packages imported (directly or indirectly) by a given Python file."""
    heuristics = [core.find_versions_from_versioncontrol,
                  lambda deps: find_versions_by_attribute(deps, executable),
                  find_versions_from_egg]
    packages = find_imported_packages(filename, executable.path, exclude_stdlib=True)
    dependencies = [Dependency.from_module(module, executable.path) for module in packages.values()]
    return core.find_versions(dependencies, heuristics)


if __name__ == "__main__":
    import sys
    from sumatra import programs
    print "\n".join(str(d) for d in find_dependencies(sys.argv[1],
                                                      programs.PythonExecutable(None),
                                                      on_changed='store-diff'))