import os
import cPickle as pickle
from datastore import FileSystemDataStore
from records import SimRecord
from formatting import get_formatter
from recordstore import DefaultRecordStore

def _remove_left_margin(s): # replace this by textwrap.dedent?
    lines = s.strip().split('\n')
    return "\n".join(line.strip() for line in lines)

class SimProject:

    def __init__(self, name, default_executable=None, default_script=None,
                 default_launch_mode=None, data_store='default', record_store='default'):
        if not os.path.exists(".smt"):
            os.mkdir(".smt")
        if os.path.exists(".smt/simulation_project"):
            raise Exception("Simulation project already exists in this directory.")
        self.name = name
        self.default_executable = default_executable
        self.default_script = default_script
        self.default_launch_mode = default_launch_mode
        if data_store == 'default':
            data_store = FileSystemDataStore()
        self.data_store = data_store # a data store object
        if record_store == 'default':
            record_store = DefaultRecordStore(".smt/simulation_records")
        self.record_store = record_store
        self._save()
        print "Simulation project successfully set up"
    
    def __del__(self):
        self._save()
    
    def _save(self):
        """Save state to some form of persistent storage. (file, database)."""
        f = open('.smt/simulation_project', 'w') # should check if file exists?
        pickle.dump(self, f)
        f.close()
    
    def info(self):
        """Show some basic information about the project."""
        template = """
        Simulation project
        ------------------
        Name                : %(name)s
        Default executable  : %(default_executable)s
        Default script      : %(default_script)s
        Default launch mode : %(default_launch_mode)s
        Data store          : %(data_store)s
        Record store        : %(record_store)s
        """
        return _remove_left_margin(template % self.__dict__)
    
    def launch_simulation(self, parameters, executable='default', script='default',
                          launch_mode='default', label=None, reason=None):
        """Launch a new simulation."""
        if executable == 'default':
            executable = self.default_executable
        if script == 'default':
            script = self.default_script
        if launch_mode == 'default':
            launch_mode = self.default_launch_mode
        sim_record = SimRecord(executable, script, parameters, launch_mode, self.data_store, label=label, reason=reason)
        sim_record.run()
        self.add_record(sim_record)
        self._save()
        return sim_record.label
    
    def add_record(self, record):
        """Add a simulation record."""
        self.record_store.save(record)
        self._most_recent = record.label
    
    def get_record(self, label):
        """Search for a record with the supplied label and return it if found.
           Otherwise return None."""
        return self.record_store.get(label)
    
    def delete_record(self, label):
        """Delete a record. Return 1 if the record is found.
           Otherwise return 0."""
        self.record_store.delete(label)
        
    def delete_group(self, label):
        """Delete a group of records. Return the number of records deleted.
           Return 0 if the label is invalid."""
        n = self.record_store.delete_group(label)
        return n
    
    def delete_by_tag(self, tag):
        """Delete all records with a given tag. Return the number of records deleted."""
        n = self.record_store.delete_by_tag(tag)
        return n
    
    def format_records(self, groups=[], format='text', mode='short', tag=None):
        # need to add filtering by tag
        records = self.record_store.list(groups)
        formatter = get_formatter(format)(records)
        return formatter.format(mode) 
    
    def most_recent(self):
        return self.get_record(self._most_recent)
    
    def add_comment(self, label, comment):
        record = self.record_store.get(label)
        record.outcome = comment
        self.record_store.save(record)
        
    def add_tag(self, label, tag):
        record = self.record_store.get(label)
        record.tags.add(tag)
        self.record_store.save(record)
    
    def remove_tag(self, label, tag):
        record = self.record_store.get(label)
        record.tags.remove(tag)
        self.record_store.save(record)
    
    
def load_simulation_project():
    if os.path.exists(".smt"):
        f = open(".smt/simulation_project", 'r')
        prj = pickle.load(f)
        f.close()
        return prj
    else:
        raise Exception("No simulation project exists in the current directory")