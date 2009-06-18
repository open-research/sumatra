import os
import pickle
from datastore import FileSystemDataStore
from recordstore import ShelveRecordStore

class SimProject:

    def __init__(self, name, default_executable=None, default_script=None,
                 default_launch_mode=None, data_store='default', record_store='default'):
        if os.path.exists(".smt"):
            raise Exception("Simulation project already exists in this directory.")
        os.mkdir(".smt")
        self.name = name
        self.default_executable = default_executable
        self.default_script = default_script
        self.default_launch_mode = default_launch_mode
        if data_store == 'default':
            data_store = FileSystemDataStore()
        self.data_store = data_store # a data store object
        if record_store == 'default':
            record_store = ShelveRecordStore(".smt/simulation_records.shelf")
        self.record_store = record_store
        self._save()
        print "Simulation project successfully set up"
        
    def _save(self):
        """Save state to some form of persistent storage. (file, database)."""
        f = open('.smt/simulation_project', 'w') # should check if file exists?
        pickle.dump(self, f)
        f.close()
    
    def info(self):
        """Show some basic information about the project."""
        pass
    
    def launch_simulation(self, parameters, executable='default', script='default',
                          launch_mode='default', label=None, reason=None):
        """Launch a new simulation."""
        if executable == 'default':
            executable = self.default_executable
        if script == 'default':
            script = self.default_script
        if launch_mode == 'default':
            launch_mode = self.default_launch_mode
        sim_record = SimRecord(executable, script, parameters, launch_mode, label=label, reason=reason)
        self.add_record(sim_record)
        sim_record.run()
    
    def add_record(self, record):
        """Add a simulation record."""
        pass
    
    def get_record(self, label):
        """Search for a record with the supplied label and return it if found.
           Otherwise return None."""
        pass
    
    def delete_record(self, label):
        """Delete a record. Return 1 if the record is found.
           Otherwise return 0."""
        pass
        
    def delete_group(self, label):
        """Delete a group of records. Return the number of records deleted.
           Return 0 if the label is invalid."""
        pass
    
    
def load_simulation_project():
    if os.path.exists(".smt"):
        return pickle.load(".smt/simulation_project")
    else:
        raise Exception("No simulation project exists in the current directory")