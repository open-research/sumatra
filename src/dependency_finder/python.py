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
find_dependencies           - returns a list of Dependency objects representing
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
from types import ModuleType
from modulefinder import Module, ModuleFinder
import imp
import distutils.sysconfig
import warnings

from sumatra.dependency_finder import core
from sumatra import versioncontrol

stdlib_path = distutils.sysconfig.get_python_lib(standard_lib=True)


def run_script(executable_path, script):
    """
    Execute a script provided as a multi-line string using the given executable,
    and evaluate the script stdout.
    """
    # if sys.executable == executable_path, we can just eval it and save the
    # process-creation overhead.
    import textwrap
    import subprocess
    p = subprocess.Popen(executable_path, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output,err = p.communicate(textwrap.dedent(script)) # should handle err
    try:
        return_value = eval(output)
    except SyntaxError, err:
        warnings.warn("Error in evaluating script output\n. Executable: %s\nScript: %s\nOutput: '%s'\nError: %s" % (executable_path, script, output, err))
        return_value = {}
    return return_value


def find_version_by_attribute(module, executable_path):
    """Try to find version information from the attributes of a Python module."""
    script = """
        import_error = None
        try:
            import %s as module
        except Exception, e:
            import_error = e  # should print this to stderr
            module = None
        version = "'unknown'"
        if module:
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
            if version is None:
                version = "'unknown'"
            if isinstance(version, tuple):
                version = ".".join(str(c) for c in version)
        print "'" + version + "'" """ % module.__name__
    return run_script(executable_path, script)


def find_version_from_egg(module, executable_path):
    """Determine whether a Python module is provided as an egg, and if so,
       obtain version information from this."""
    version = 'unknown'
    dir = os.path.dirname(module.__file__)
    if os.path.isdir(dir):
        if 'EGG-INFO' in os.listdir(dir):
            with open(os.path.join(dir, 'EGG-INFO', 'PKG-INFO')) as f:
                for line in f.readlines():
                    if line[:7] == 'Version':
                        version = line.split(' ')[1].strip()
                        attr_name = 'egg-info'
                        break        
    return version


def find_version_from_versioncontrol(module, executable_path):
    """Determine whether a Python module is under version control, and if so,
       obtain version information from this."""
    if hasattr(module, "__path__"):
        real_path = os.path.realpath(module.__path__[0]) # resolve any symbolic links
    else:
        real_path = os.path.realpath(os.path.dirname(module.__file__))
    return core.find_version_from_versioncontrol(real_path)

# Other possible heuristics:
#   * check for an egg-info file with a similar name to the module
#     although this is not really safe, as there can be old egg-info files
#     lying around.
#   * could also look in the __init__.py for a Subversion $Id:$ tag


heuristics = [find_version_from_versioncontrol,
              find_version_by_attribute,
              find_version_from_egg]


class Dependency(core.BaseDependency):
    """
    Contains information about a Python module or package, and tries to
    determine version information.
    """
    module = 'python'
    
    def __init__(self, module_name, path, version, diff=''):
        self.name = module_name
        self.path = path
        self.in_stdlib = os.path.dirname(self.path) == stdlib_path
        self.diff = diff
        self.version = version
    
    @classmethod
    def from_module(cls, module, executable_path, on_changed='error'):
        """Create from modulefinder.Module instance."""
        try:
            version = core.find_version(module, heuristics, executable_path)
        except versioncontrol.UncommittedModificationsError:
            if on_changed == 'error':
                raise
            elif on_changed == 'store-diff':
                wc = versioncontrol.get_working_copy(m.__path__[0])
                version = wc.current_version()
                diff = wc.diff()
            else:
                raise Exception("Only 'error' and 'store-diff' are currently supported for on_changed.")
        return cls(module.__name__, module.__path__, version, diff)
    
    #def _import(self):
    #    self.import_error = None
    #    try:
    #        m = __import__(self.name)
    #    except Exception, e:
    #        self.import_error = e
    #        m = None
    #    return m

def find_imported_packages(filename, executable_path, debug=0):
    """
    Find all imported top-level packages for a given Python file.
    
    We cannot assume that the version of Python being used to run Sumatra is the
    same as that used to run the simulation/analysis. Therefore we need to run
    all the dependency finding and version checking in a subprocess with the
    correct version of Python.
    """
    #Actually, we could check whether executable_path matches sys.executable, and
    #then do it in this process. On the other hand, the dependency finding
    #could run in parallel with the simulation (could for multicore): we could
    #move setting of dependencies to after the simulation, rather than having it
    #in record.register()
    #import textwrap
    #import subprocess
    #p = subprocess.Popen(executable_path, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    #output,err = p.communicate(textwrap.dedent("""
    #                from modulefinder import ModuleFinder
    #                import sys
    #                finder = ModuleFinder(path=sys.path, debug=%d)
    #                finder.run_script("%s")
    #                top_level_packages = {}
    #                for name, module in finder.modules.items():
    #                    if module.__path__ and "." not in name:
    #                        top_level_packages[name] = module
    #                print top_level_packages""" % (int(debug), filename)))
    #try:
    #    top_level_packages = eval(output)
    #except SyntaxError:
    #    warnings.warn("Unable to determine imported packages for %s with %s. Output was: '%s'" % (filename, executable_path, output))
    #    top_level_packages = {}
    #return top_level_packages
    script = """
        from modulefinder import ModuleFinder
        import sys
        finder = ModuleFinder(path=sys.path, debug=%d)
        finder.run_script("%s")
        top_level_packages = {}
        for name, module in finder.modules.items():
            if module.__path__ and "." not in name:
                top_level_packages[name] = module
        print top_level_packages""" % (int(debug), filename)
    return run_script(executable_path, script)


def find_dependencies(filename, executable_path, on_changed):
    """Return a list of Dependency objects representing all the top-level
       modules or packages imported (directly or indirectly) by a given Python file."""
    packages = find_imported_packages(filename, executable_path)
    dependencies = [Dependency.from_module(module, executable_path, on_changed=on_changed) for module in packages.values()]
    return [d for d in dependencies if not d.in_stdlib]


if __name__ == "__main__":
    import sys
    from sumatra import programs
    print "\n".join(str(d) for d in find_dependencies(sys.argv[1],
                                                      programs.PythonExecutable(None),
                                                      on_changed='store-diff'))