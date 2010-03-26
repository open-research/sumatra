"""
The programs module handles simulator programs, i.e. executable files, to
support the ability to customize Sumatra's behaviour for specific simulators.

Classes
-------

Executable       - represents a generic executable, about which nothing is known
                   except its name. The base class for specific simulator classes.
NESTSimulator    - represents the NEST neuroscience simulator.
NEURONSimulator  - represents the NEURON neuroscience simulator.
PythonExecutable - represents the Python interpreter executable.

Functions
---------

get_executable()      - Return an appropriate subclass of Executable, given
                        either the path to an executable file or a script file
                        that can be run with a given simulator.
register_executable() - Register new subclasses of Executable that can be
                        returned by get_executable().
"""

import os.path
import re
import subprocess

version_pattern = re.compile(r'\b(?P<version>\d[\.\d]*([a-z]*\d)*)\b')

class VersionedProgram(object):
    pass
    
        
class Executable(VersionedProgram): # call this Simulator? what about PyNEST?
    # store compilation/configuration options?

    def __init__(self, path, version=None):
        VersionedProgram.__init__(self)
        if not hasattr(self, 'name'):
            self.name = os.path.basename(path)
        if path and os.path.exists(path):
            self.path = path
        else:
            self.path = self._find_executable(path or self.default_executable_name)    
        if not hasattr(self, 'name'):
            self.name = os.path.basename(self.path)
        self.version = version or self._get_version()

    def __str__(self):
        return "%s (version: %s) at %s" % (self.name, self.version, self.path)

    def _find_executable(self, executable_name):
        found = []
        for path in os.getenv('PATH').split(':'):
            if os.path.exists(os.path.join(path, executable_name)):
                found += [path] 
        if not found:
            raise Exception('%s could not be found. Please supply the path to the %s executable.' % (self.name, executable_name))
        else:
            executable = os.path.join(found[0], executable_name) 
            if len(found) == 1:
                print 'Using', executable
            else:
                print 'Multiple versions found, using %s. If you wish to use a different version, please specify it explicitly' % executable
        return executable

    def _get_version(self):
        p = subprocess.Popen("%s --version" % self.path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        returncode = p.wait()
        match = version_pattern.search(p.stdout.read())
        if match:
            version = match.groupdict()['version']
        else:
            version = None
        return version

    def __eq__(self, other):
        return type(self) == type(other) and self.path == other.path and self.name == other.name and self.version == other.version
    
    def __ne__(self, other):
        return not self.__eq__(other)
    

class NEURONSimulator(Executable):
    
    name = "NEURON"
    default_executable_name = "nrniv"
    

class PythonExecutable(Executable):
    
    name = "Python"
    default_executable_name = "python"
    
    @staticmethod
    def write_parameters(parameters, filename):
        parameters.save(filename)


class NESTSimulator(Executable):
    
    name = "NEST"
    default_executable_name = 'nest'
    
    

    
registered_program_names = {}
registered_executables = {}
registered_extensions = {}
    
def register_executable(cls, name, executable, extensions):
    assert issubclass(cls, Executable)
    registered_program_names[name] = cls
    registered_executables[executable] = cls
    for ext in extensions:
        registered_extensions[ext] = cls
    
register_executable(NEURONSimulator, 'NEURON', 'nrniv', ('.hoc', '.oc'))
register_executable(PythonExecutable, 'Python', 'python', ('.py',))
register_executable(NESTSimulator, 'NEST', 'nest', ('.sli',))
    
def get_executable(path=None, script_file=None):
    """
    Given the path to an executable, determine what program it is, if possible.
    Given the name of a script file, try to infer the program that runs that
    script.
    Return an appropriate subclass of Executable
    """
    if path:
        prog_name = os.path.basename(path)
        if prog_name in registered_executables:
            program = registered_executables[prog_name](path)
        else:
            program = Executable(path)
    elif script_file:
        script_path, ext = os.path.splitext(script_file)
        if ext in registered_extensions:
            program = registered_extensions[ext](path)
        else:
            raise Exception("Extension not recognized.")
    else:
        raise Exception('Either path or script_file must be specified')
        
    return program