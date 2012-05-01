"""
The programs module handles simulator and analysis programs, i.e. executable
files, to support the ability to customize Sumatra's behaviour for specific tools.

Classes
-------

Executable       - represents a generic executable, about which nothing is known
                   except its name. The base class for specific simulator/
                   analysis tool classes.
NESTSimulator    - represents the NEST neuroscience simulator.
NEURONSimulator  - represents the NEURON neuroscience simulator.
PythonExecutable - represents the Python interpreter executable.

Functions
---------

get_executable()      - Return an appropriate subclass of Executable, given
                        either the path to an executable file or a script file
                        that can be run with a given tool.
register_executable() - Register new subclasses of Executable that can be
                        returned by get_executable().
"""
from __future__ import with_statement
import os.path
import re
import subprocess
import sys

version_pattern = re.compile(r'\b(?P<version>\d[\.\d]*([a-z]*\d)*)\b')


class Executable(object):
    # store compilation/configuration options? yes, if we can determine them

    def __init__(self, path, version=None, options=""):
        if not hasattr(self, 'name'):
            self.name = os.path.basename(path)
        if path and os.path.exists(path):
            self.path = path
        else:
            try:
                self.path = self._find_executable(path or self.default_executable_name)
            except Warning, errmsg:
                print errmsg
                self.path = path
        if not hasattr(self, 'name'):
            self.name = os.path.basename(self.path)
        self.version = version or self._get_version()
        self.options = options

    def __str__(self):
        s = "%s (version: %s) at %s" % (self.name, self.version, self.path)
        if self.options:
            s += "options: %s" % self.options
        return s

    def _find_executable(self, executable_name):
        found = []
        if sys.platform == 'win32' or sys.platform == 'win64':
            executable_name = executable_name + '.exe'
            path_token = ';'
        else:
            path_token = ':'
        for path in os.getenv('PATH').split(path_token):
            if os.path.exists(os.path.join(path, executable_name)):
                found += [path] 
        if not found:
            raise Warning('%s could not be found. Please supply the path to the %s executable.' % (self.name, executable_name))
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
        return type(self) == type(other) and self.path == other.path and self.name == other.name and self.version == other.version and self.options == other.options
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __getstate__(self):
        return {'path': self.path, 'version': self.version, 'options': self.options}
    
    @staticmethod
    def write_parameters(parameters, filename):
        parameters.save(filename)


class NEURONSimulator(Executable):
    
    name = "NEURON"
    default_executable_name = "nrniv"
    mpi_options = "-mpi"
    pre_run = "nrnivmodl"

    @staticmethod
    def write_parameters(parameters, filename):
        with open(filename, 'w') as fp:
            for name, value in parameters.as_dict().items():
                if isinstance(value, basestring):
                    fp.write('strdef %s\n' % name)
                    fp.write('%s = "%s"\n' % (name, value))
                else:
                    fp.write('%s = %g\n' % (name, value))


class PythonExecutable(Executable):
    
    name = "Python"
    default_executable_name = "python" 


class NESTSimulator(Executable):
    
    name = "NEST"
    default_executable_name = 'nest'
    

class GENESISSimulator(Executable):
    
    name = "GENESIS"
    default_executable_name = "genesis"

    def _get_version(self):
        print "Writing genesis version script"
        with open("genesis_version.g", "w") as fd:
            fd.write("""openfile genesis_version.out w
                        writefile genesis_version.out {version}
                        closefile genesis_version.out
                        quit
                    """)
        p = subprocess.Popen("%s genesis_version.g" % self.path, shell=True) #stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True)
        returncode = p.wait()
        print returncode
        with open("genesis_version.out") as fd:
            version = fd.read()
        os.remove("genesis_version.g")
        os.remove("genesis_version.out")
        return version.strip()
    
registered_program_names = {}
registered_executables = {}
registered_extensions = {}
    
def register_executable(cls, name, executables, extensions):
    """Register a new subclass of Executable that can be returned by get_executable()."""
    assert issubclass(cls, Executable)
    registered_program_names[name] = cls
    for executable in executables:
        registered_executables[executable] = cls
    for ext in extensions:
        registered_extensions[ext] = cls
    
register_executable(NEURONSimulator, 'NEURON', ('nrniv', 'nrngui'), ('.hoc', '.oc'))
register_executable(PythonExecutable, 'Python', ('python', 'python2', 'python3',
                                                 'python2.5', 'python2.6', 'python2.7',
                                                 'python3.1', 'python3.2'), ('.py',))
register_executable(NESTSimulator, 'NEST', ('nest',), ('.sli',))
register_executable(GENESISSimulator, 'GENESIS', ('genesis',), ('.g',))
    
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
