from __future__ import with_statement
from types import ModuleType
from modulefinder import ModuleFinder
import imp
import distutils.sysconfig
import os
import sys

stdlib_path = distutils.sysconfig.get_python_lib(standard_lib=True)


def find_version_by_attribute(module):
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

heuristics = [find_version_by_attribute, find_version_from_egg]

def find_version(module, extra_heuristics=[]):
    heuristics.extend(extra_heuristics)
    for heuristic in heuristics:
        version = heuristic(module)
        if version is not 'unknown':
            break
    return str(version)
        
    version = find_version_by_attribute(module)
    # next, check if the module is a .egg
    if version == 'unknown':
        version = find_version_from_egg(module)
    # next, could check for an egg-info file with a similar name to the module
    # although this is not really safe, as there can be old egg-info files
    # lying around.
    
    # could also look in the __init__.py for a Subversion $Id:$ tag
    return version

def find_imported_packages(filename):
    """Find all imported top-level packages for a given Python file."""
    finder = ModuleFinder(path=sys.path[1:], debug=2)
    # note that we remove the first element of sys.path to stop modules in the
    # sumatra source directory with the same name as standard library modules,
    # e.g. commands, being loaded when the standard library module was wanted.
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
    
    def __init__(self, module_name, path=None, version=None):
        self.name = module_name
        if path:
            self.path = path
        else:
            file_obj, self.path, description = imp.find_module(self.name)
        self.in_stdlib = os.path.dirname(self.path) == stdlib_path
        if version:
            self.version = version
        else:
            m = self._import()
            if m:
                self.version = find_version(m)
            else:
                self.version = 'unknown'
    
    def __repr__(self):
        return "%s (%s) version=%s" % (self.name, self.path, self.version)
    
    def _import(self):
        self.import_error = None
        try:
            m = __import__(self.name)
        except ImportError, e:
            self.import_error = e
            m = None
        return m
        
        
def find_dependencies_python(filename):
    packages = find_imported_packages(filename)
    dependencies = [Dependency(name) for name in packages]
    return [d for d in dependencies if not d.in_stdlib]

def find_dependencies(filename, executable):
    if executable.name == "Python":
        return find_dependencies_python(filename)
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
    print "\n".join(str(d) for d in find_dependencies(sys.argv[1]))
