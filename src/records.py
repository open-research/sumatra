
from datetime import datetime

class SimRecord(object): # maybe just call this Simulation
    
    def __init__(self, executable, script, parameters, launch_mode, label=None, reason=None):
        self.label = label
        self.reason = reason
        self.duration = None
        self.executable = executable # an Executable object incorporating path, version, maybe system information
        self.script = script # a Script object incorporating path and version (and maybe version of all imported modules as well)
        self.parameters = parameters # a ParameterSet object
        self.launch_mode = launch_mode # a launch_mode object - basically, run serially or with MPI. If MPI, what configuration
        self.outcome = None
        self.timestamp = datetime.now() # might need to allow for this to be set as argument to allow for distributed/batch simulations on machines with out-of-sync clocks
        
    def run(self):
        """Launch the simulation."""
        # if it hasn't been run already. Do we need to distinguish separate Simulation and SimRecord classes?
        pass
    