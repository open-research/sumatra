"""
Handles storage of simulation/analysis records based on the Python standard
shelve module.

:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from sumatra.recordstore.base import RecordStore
from sumatra.recordstore import serialization
import shelve
from datetime import datetime


def check_name(f):
    """
    Some backends to shelve do not accept unicode variables as keys.
    This decorator therefore converts a unicode project_name to a string
    before calling the wrapped method. See http://bugs.python.org/issue1036490
    """

    def wrapped(self, project_name, *args):
        project_name = str(project_name)
        return f(self, project_name, *args)
    return wrapped


class ShelveRecordStore(RecordStore):
    """
    Handles storage of simulation/analysis records based on the Python standard
    :mod:`shelve` module.

    The advantage of this record store is that it has no dependencies. The
    disadvantages are that it allows only local access and does not support
    the *smtweb* interface.
    """

    def __init__(self, shelf_name=".smt/records"):
        self._shelf_name = shelf_name
        self.shelf = shelve.open(shelf_name)

    def __del__(self):
        if hasattr(self, "shelf"):
            self.shelf.close()

    def __str__(self):
        return "Record store using the shelve package (database file=%s)" % self._shelf_name

    def __getstate__(self):
        return {'shelf_name': self._shelf_name}

    def __setstate__(self, state):
        self.__init__(**state)

    def list_projects(self):
        return self.shelf.keys()

    @check_name
    def save(self, project_name, record):
        if self.shelf.has_key(project_name):
            records = self.shelf[project_name]
        else:
            records = {}
        records[record.label] = record
        self.shelf[project_name] = records

    @check_name
    def get(self, project_name, label):
        return self.shelf[project_name][label]

    @check_name
    def list(self, project_name, tags=None):
        if project_name in self.shelf:
            if tags:
                if not hasattr(tags, "__iter__"):
                    tags = [tags]
                records = set()
                for tag in tags:
                    records = records.union([record for record in self.shelf[project_name].values() if tag in record.tags])
                records = list(records)
            else:
                records = self.shelf[project_name].values()
        else:
            records = []
        return records

    @check_name
    def labels(self, project_name):
        if project_name in self.shelf:
            return self.shelf[project_name].keys()
        else:
            return []

    @check_name
    def delete(self, project_name, label):
        records = self.shelf[project_name]
        records.pop(label)
        self.shelf[project_name] = records

    @check_name
    def delete_by_tag(self, project_name, tag):
        for_deletion = [record for record in self.shelf[project_name].values() if tag in record.tags]
        for record in for_deletion:
            self.delete(project_name, record.label)
        return len(for_deletion)

    @check_name
    def most_recent(self, project_name):
        most_recent = None
        most_recent_timestamp = datetime.min
        for record in self.shelf[project_name].itervalues():
            if record.timestamp > most_recent_timestamp:
                most_recent_timestamp = record.timestamp
                most_recent = record.label
        return most_recent
