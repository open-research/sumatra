from datetime import datetime
import time
from formatting import get_formatter

def assert_equal(a, b, msg=''):
    assert a == b, "%s: %s %s != %s %s" % (msg, a, type(a), b, type(b))

class SimRecord(object): # maybe just call this Simulation
    
    def __init__(self, executable, repository, main_file, version, parameters,
                 launch_mode, datastore, label=None, reason=None):
        self.group = label
        self.reason = reason
        self.duration = None
        self.executable = executable # an Executable object incorporating path, version, maybe system information
        self.repository = repository # a Repository object
        self.main_file = main_file
        self.version = version
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
        # Check the code hasn't changed and the version is correct
        assert not self.repository.working_copy.has_changed()
        assert_equal(self.repository.working_copy.current_version(), self.version, "version") 
        # run pre-simulation tasks, e.g. nrnivmodl
        self.launch_mode.pre_run(self.executable)
        # Write the simulator-specific parameter file
        parameter_file = "%s.param" % self.label
        self.executable.write_parameters(self.parameters, parameter_file)
        # Run simulation
        start_time = time.time()        
        result = self.launch_mode.run(self.executable, self.main_file, parameter_file)
        self.duration = time.time() - start_time
        # Run post-processing scripts
        pass # skip this if there is an error
        # Search for newly-created datafiles
        self.data_key = self.datastore.find_new_files(self.timestamp)
        print "Data key is", self.data_key
    
    def describe(self, format='text', mode='long'):
        formatter = get_formatter(format)([self])
        return formatter.format(mode)
    