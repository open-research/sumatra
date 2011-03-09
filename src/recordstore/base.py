"""
Provides base RecordStore class.
"""

from sumatra.recordstore import serialization

class RecordStore(object):
    
    def list_projects(self):
        raise NotImplementedError

    def save(self, project_name, record):
        raise NotImplementedError
        
    def get(self, project_name, label):
        raise NotImplementedError
    
    def list(self, project_name, tags=None):
        raise NotImplementedError
    
    def labels(self, project_name):
        raise NotImplementedError
    
    def delete(self, project_name, label):
        raise NotImplementedError
        
    def delete_by_tag(self, project_name, tag):
        raise NotImplementedError
        
    def most_recent(self, project_name):
        raise NotImplementedError
    
    def export(self, project_name, indent=2):
        """Export store contents as JSON."""
        return "[" + ",\n".join(serialization.encode_record(record, indent=indent)
                                for record in self.list(project_name)) + "]"

    def import_(self, project_name, content):
        """Import records in JSON format."""
        records = serialization.decode_records(content)
        for record in records:
            # need to check for duplicate record labels?
            self.save(project_name, record)

    def sync(self, other, project_name):
        """
        Synchronize two record stores so that they contain the same records for
        a given project.
        
        Where the two stores have the same label (within a project) for
        different records, those records will not be synced. The method
        returns a list of non-synchronizable records (empty if the sync worked
        perfectly).
        """
        # what to do about syncing different Sumatra versions? Need to think about
        # schema versioning
        self_labels = set(self.labels(project_name))
        other_labels = set(other.labels(project_name))
        only_in_self = self_labels.difference(other_labels)
        only_in_other = other_labels.difference(self_labels)
        in_both = self_labels.intersection(other_labels)
        non_synchronizable = []
        for label in in_both:
            if self.get(project_name, label) != other.get(project_name, label):
                non_synchronizable.append(label)
        for label in only_in_self:
            other.save(project_name, self.get(project_name, label))
        for label in only_in_other:
            self.save(project_name, other.get(project_name, label))
        return non_synchronizable
    
    def sync_all(self, other):
        all_projects = set(self.list_projects()).union(other.list_projects())
        for project_name in all_projects:
            self.sync(other, project_name)
