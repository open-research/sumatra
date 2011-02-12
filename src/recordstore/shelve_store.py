"""
Handles storage of simulation/analysis records based on the Python standard
shelve module.
"""

from sumatra.recordstore import RecordStore
import shelve
from datetime import datetime


class ShelveRecordStore(RecordStore):
    
    def __init__(self, shelf_name=".smt/records"):
        self._shelf_name = shelf_name
        self.shelf = shelve.open(shelf_name)
        
    def __del__(self):
        self.shelf.close()
        
    def __str__(self):
        return "Record store using the shelve package (database file=%s)" % self._shelf_name
        
    def __getstate__(self):
        return self._shelf_name
    
    def __setstate__(self, state):
        self.__init__(state)

    def list_projects(self):
        return self.shelf.keys()

    def save(self, project_name, record):
        if self.shelf.has_key(project_name):
            records = self.shelf[project_name]
        else:
            records = {}
        records[record.label] = record
        self.shelf[project_name] = records
        
    def get(self, project_name, label):
        return self.shelf[project_name][label]
    
    def list(self, project_name, tags=None):
        if tags:
            if not hasattr(tags, "__iter__"):
                tags = [tags]
            records = set()
            for tag in tags:
                records = records.union([record for record in self.shelf[project_name].values() if tag in record.tags])
            records = list(records)
        else:
            records = self.shelf[project_name].values()
        return records
    
    def labels(self, project_name):
        return self.shelf[project_name].keys()
    
    def delete(self, project_name, label):
        records = self.shelf[project_name]
        records.pop(label)
        self.shelf[project_name] = records
        
    def delete_by_tag(self, project_name, tag):
        for_deletion = [record for record in self.shelf[project_name].values() if tag in record.tags]
        for record in for_deletion:
            self.delete(project_name, record.label)
        return len(for_deletion)
        
    def most_recent(self, project_name):
        most_recent = None
        most_recent_timestamp = datetime.min
        for record in self.shelf[project_name].itervalues():
            if record.timestamp > most_recent_timestamp:
                most_recent_timestamp = record.timestamp
                most_recent = record.label
        return most_recent
