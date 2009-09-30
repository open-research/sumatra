import os
import sys
from datetime import datetime
import time
import subprocess
from formatting import get_formatter

class SimRecord(object): # maybe just call this Simulation
    
    def __init__(self, executable, script, parameters, launch_mode, datastore, label=None, reason=None):
        self.group = label
        self.reason = reason
        self.duration = None
        self.executable = executable # an Executable object incorporating path, version, maybe system information
        self.script = script # a Script object incorporating path and version (and maybe version of all imported modules as well)
        self.parameters = parameters # a ParameterSet object
        self.launch_mode = launch_mode # a launch_mode object - basically, run serially or with MPI. If MPI, what configuration
        self.datastore = datastore
        self.outcome = None
        self.data_key = None
        self.timestamp = datetime.now() # might need to allow for this to be set as argument to allow for distributed/batch simulations on machines with out-of-sync clocks
        self.tags = set()
    
    @property
    def label(self):
        return "%s_%s" % (self.group, self.timestamp.strftime("%Y%m%d-%H%M%S"))        
        
    def run(self):
        """Launch the simulation."""
        # if it hasn't been run already. Do we need to distinguish separate Simulation and SimRecord classes?
        # Check if the working copy has modifications and prompt to commit or revert them
        if self.script.has_changed():
            raise Exception("Code has changed, please commit your changes")
        # Check out the requested code version, if necessary
        self.script.update_code()        
        # run pre-simulation tasks, e.g. nrnivmodl
        pass
        # Write the simulator-specific parameter file
        parameter_file = "%s.param" % self.label
        self.executable.write_parameters(self.parameters, parameter_file)
        # Run simulation
        cmd = "%s %s %s" % (self.executable.default_executable_name, self.script.main_file, parameter_file)
        start_time = time.time()
        print "Sumatra is running the following command:", cmd
        #p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None, close_fds=True)
        result = p.wait() 
        #self.errors = p.stderr.read()
        #self.output = p.stdout.read()
        #sys.stdout.write(self.output)
        #sys.stderr.write(self.errors)
        self.duration = time.time() - start_time
        # Run post-processing scripts
        pass # skip this if there is an error
        # Search for newly-created datafiles
        self.data_key = self.datastore.find_new_files(self.timestamp)
        print "Data key is", self.data_key
        
    def code_version(self):
        return self.script.version
    
    def describe(self, format='text', mode='long'):
        formatter = get_formatter(format)([self])
        return formatter.format(mode)
    