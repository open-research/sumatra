"""
The programs module handles simulator and analysis programs, i.e. executable
files, to support the ability to customize Sumatra's behaviour for specific tools.

Classes
-------

Executable
    represents a generic executable, about which nothing is known except its
    name. The base class for specific simulator/analysis tool classes.
PythonExecutable
    represents the Python interpreter executable.
MatlabExecutable
    represents the Matlab interpreter executable.
NESTSimulator
    represents the NEST neuroscience simulator.
NEURONSimulator
    represents the NEURON neuroscience simulator.
GENESISSimulator
    represents the GENESIS neuroscience simulator.
RExecutable
    represents the Rscript CLI to R interpreter executable.

Functions
---------

get_executable()
    Return an appropriate subclass of Executable, given either the path to an
    executable file or a script file that can be run with a given tool.


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from __future__ import with_statement
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import os.path
import re
import sys
import warnings
from .core import run, _Registry


version_pattern = re.compile(r'\b(?P<version>\d+(\.\d+){1,2}(\.?[a-z]+\d?)?)\b')
version_pattern_matlab = re.compile(r'(?<=SMT_DETECT_MATLAB_VERSION=)(?P<version>\d.+)\b')


class Executable(object):
    # store compilation/configuration options? yes, if we can determine them
    requires_script = False  # does this executable require a script file
    required_attributes = ("executable_names", "file_extensions",)
    name = None

    def __init__(self, path, version=None, options="", name=None):
        if path and os.path.exists(path):
            self.path = path
        else:
            try:
                self.path = self._find_executable(path or self.default_executable_name)
            except Warning as errmsg:
                warnings.warn(errmsg)
                self.path = path
        if self.name is None:
            self.name = name or os.path.basename(self.path)
        self.version = version or self._get_version()
        self.options = options

    def __repr__(self):
        s = "%s (version: %s) at %s" % (self.name, self.version, self.path)
        if self.options:
            s += " options: %s" % self.options
        return s

    def _find_executable(self, executable_name):
        found = []
        if sys.platform == 'win32' or sys.platform == 'win64':
            executable_name = executable_name + '.exe'
        for path in os.getenv('PATH').split(os.path.pathsep):
            if os.path.exists(os.path.join(path, executable_name)):
                found += [path]
        if not found:
            raise Warning('%s could not be found. Please supply the path to the %s executable.' % (self.name, executable_name))
        else:
            executable = os.path.join(found[0], executable_name)
            if len(found) == 1:
                print('Using %s' % executable)
            else:
                print('Multiple versions found, using %s. If you wish to use a different version, please specify it explicitly' % executable)
        return executable

    def _get_version(self):
        returncode, output, err = run("%s --version" % self.path,
                                      shell=True, timeout=5)
        match = version_pattern.search(output + err)
        if match:
            version = match.groupdict()['version']
        else:
            version = "unknown"
        return version

    def __eq__(self, other):
        return type(self) == type(other) and self.path == other.path and self.name == other.name and self.version == other.version and self.options == other.options

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getstate__(self):
        return {'path': self.path, 'version': self.version, 'options': self.options, 'name': self.name}

    def __setstate__(self, d):
        self.__dict__ = d

    @staticmethod
    def write_parameters(parameters, filebasename):
        filename = parameters.save(filebasename, add_extension=True)
        return filename


class NEURONSimulator(Executable):
    name = "NEURON"
    executable_names = ('nrniv', 'nrngui')
    file_extensions = ('.hoc', '.oc')
    default_executable_name = "nrniv"
    mpi_options = "-mpi"
    pre_run = "nrnivmodl"
    requires_script = True

    @staticmethod
    def write_parameters(parameters, filebasename):
        filename = filebasename + ".hoc"
        with open(filename, 'w') as fp:
            for name, value in parameters.as_dict().items():
                if isinstance(value, str):
                    fp.write('strdef %s\n' % name)
                    fp.write('%s = "%s"\n' % (name, value))
                else:
                    fp.write('%s = %g\n' % (name, value))
        return filename


class PythonExecutable(Executable):
    name = "Python"
    executable_names = ('python', 'python2', 'python3', 'python2.5',
                        'python2.6', 'python2.7', 'python3.1', 'python3.2',
                        'python3.3', 'python3.4')
    file_extensions = ('.py',)
    default_executable_name = "python"
    requires_script = True


class MatlabExecutable(Executable):
    name = "Matlab"
    executable_names = ('matlab',)
    file_extensions = ('.m',)
    default_executable_name = "matlab"
    requires_script = True

    def _get_version(self):
        returncode, output, err = run("matlab -nodesktop -nosplash -nojvm -r \"disp(['SMT_DETECT_MATLAB_VERSION=' version()]);quit\"",
                                      shell=True)
        match = version_pattern_matlab.search(output + err)
        if match:
            version = match.groupdict()['version']
        else:
            version = "unknown"
        return version

class RExecutable(Executable):
    name = "R"
    executable_names = ('Rscript')
    file_extensions = ('.R', '.r')
    default_executable_name = "Rscript"
    requires_script = True

class NESTSimulator(Executable):
    name = "NEST"
    executable_names = ('nest',)
    file_extensions = ('.sli',)
    default_executable_name = 'nest'
    requires_script = True


class GENESISSimulator(Executable):
    name = "GENESIS"
    executable_names = ('genesis',)
    file_extensions = ('.g',)
    default_executable_name = "genesis"
    requires_script = True

    def _get_version(self):
        print("Writing genesis version script")
        with open("genesis_version.g", "w") as fd:
            fd.write("""openfile genesis_version.out w
                        writefile genesis_version.out {version}
                        closefile genesis_version.out
                        quit
                    """)
        returncode, output, err = run("%s genesis_version.g" % self.path, shell=True)
        with open("genesis_version.out") as fd:
            version = fd.read()
        os.remove("genesis_version.g")
        os.remove("genesis_version.out")
        return version.strip()


_Registry().add_component_type(Executable)
_Registry().register(NEURONSimulator)
_Registry().register(PythonExecutable)
_Registry().register(MatlabExecutable)
_Registry().register(NESTSimulator)
_Registry().register(GENESISSimulator)
_Registry().register(RExecutable)


def get_executable(path=None, script_file=None):
    """
    Given the path to an executable, determine what program it is, if possible.
    Given the name of a script file, try to infer the program that runs that
    script.
    Return an appropriate subclass of Executable
    """
    if path:
        prog_name = os.path.basename(path)
        program = Executable(path)
        for executable_type in _Registry().components[Executable].values():
            if prog_name in executable_type.executable_names:
                program = executable_type(path)
    elif script_file:
        script_path, ext = os.path.splitext(script_file)
        program = None
        for executable_type in _Registry().components[Executable].values():
            if ext in executable_type.file_extensions:
                program = executable_type(path)
        if program is None:
            raise Exception("Extension not recognized.")
    else:
        raise Exception('Either path or script_file must be specified')
    return program
