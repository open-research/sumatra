"""
Handles storage of simulation records based on the Python standard shelve
module.
"""

from sumatra.recordstore import RecordStore
import shelve

class ShelveRecordStore(RecordStore):
    
    def __init__(self, shelf_name=".smt/simulation_records"):
        self._shelf_name = shelf_name
        self.shelf = shelve.open(shelf_name)
        
    def __del__(self):
        self.shelf.close()
        
    def __str__(self):
        return "shelve"
        
    def __getstate__(self):
        return self._shelf_name
    
    def __setstate__(self, state):
        self.__init__(state)

    def save(self, project, record):
        if self.shelf.has_key(project.name):
            records = self.shelf[project.name]
        else:
            records = {}
        records[record.label] = record
        self.shelf[project.name] = records
        
    def get(self, project, label):
        return self.shelf[project.name][label]
    
    def list(self, project, groups):
        if groups:
            return [record for record in self.shelf[project.name].values() if record.group in groups]
        else:
            return self.shelf[project.name].values()
    
    def delete(self, project, label):
        records = self.shelf[project.name]
        records.pop(label)
        self.shelf[project.name] = records
        
    def delete_group(self, project, group_label):
        for_deletion = [record for record in self.shelf[project.name].values() if record.group==group_label]
        for record in for_deletion:
            self.delete(project, record.label)
        return len(for_deletion)
        
    def delete_by_tag(self, project, tag):
        raise NotImplementedError