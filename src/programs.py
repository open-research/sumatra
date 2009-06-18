import os.path



class VersionedProgram(object):
    
    def __init__(self, path, name=None):
        self.path = path
        self.name = name # inferred from path if not given

        
class Executable(VersionedProgram): # call this Simulator? what about PyNEST?
    # store compilation/configuration options?

    def __init__(self, path):
        self.path = path or self._find_executable()    

    def _find_executable(self):
        found = []
        for path in os.getenv('PATH').split(':'):
            if os.path.exists(os.path.join(path, self.default_executable_name)):
                found += [path] 
        if not found:
            raise Exception('%s could not be found. Please supply the path to the %s executable.' % (self.name, self.default_executable_name))
        else:
            executable = os.path.join(found[0], self.default_executable_name) 
            if len(found) == 1:
                print 'Using', executable
            else:
                print 'Multiple versions found, using %s\n \
                       If you wish to use a different version, please specify it explicitly' % executable
        return executable

class NEURONSimulator(Executable):
    
    name = "NEURON"
    default_executable_name = "nrniv"
    

class PythonExecutable(Executable):
    
    name = "Python"
    default_executable_name = "python"

class NESTSimulator(Executable):
    
    name = "NEST"
    default_executable_name = 'nest'
    

class Script(VersionedProgram): # call this SimulationCode?
    # note that a script need not be a single file, but could be a suite of files
    # generally, should define a RCS repository and a main file
    pass
    # store reference to the executable for which the script is destined?
    
    
registered_programs = {
    'nrniv': NEURONSimulator,
    'python': PythonExecutable,
    'nest': NESTSimulator,
}

registered_extensions = {
    '.py': PythonExecutable,
    '.hoc': NEURONSimulator,
    '.oc': NEURONSimulator,
    '.sli': NESTSimulator
}
    
def register_executable(name, cls):
    assert issubclass(cls, Executable)
    registered_programs[name] = cls
    
def register_extension(ext, cls):
    assert issubclass(cls, Executable)
    registered_extensions[ext] = cls
    
def get_executable(path=None, script_file=None):
    """
    Given the path to an executable, determine what program it is, if possible.
    Given the name of a script file, try to infer the program that runs that
    script.
    Return an appropriate subclass of Executable
    """
    if path:
        prog_name = os.path.basename(path)
        if prog_name in registered_programs:
            program = registered_programs[prog_name](path)
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