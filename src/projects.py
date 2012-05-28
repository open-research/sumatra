"""
The projects module defines the Project class, which stores information
about a computation-based project and contains a number of methods for managing
and running computational experiments, whether simulations, analyses or whatever.
This is the main class that is used directly when using Sumatra within your own
scripts.

Classes
-------

Project - stores information about a computational project, and enables
          launching, annotating, deleting and retrieving information about
          simulation/analysis runs.

Functions
---------

load_project() - read project information from the working directory and return
                 a Project object.
"""

import os
import sys
import cPickle as pickle
from copy import deepcopy
from sumatra.records import Record
from sumatra import programs, datastore
from sumatra.formatting import get_formatter, get_diff_formatter
from sumatra.recordstore import DefaultRecordStore
from sumatra.versioncontrol import UncommittedModificationsError, get_working_copy
import mimetypes
try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_PROJECT_FILE = "project"
RECORDS_PER_PAGE = 50

def _remove_left_margin(s): # replace this by textwrap.dedent?
    lines = s.strip().split('\n')
    return "\n".join(line.strip() for line in lines)

def _get_project_file(path):
    return os.path.join(path, ".smt", DEFAULT_PROJECT_FILE)


class Project(object):

    def __init__(self, name, default_executable=None, default_repository=None,
                 default_main_file=None, default_launch_mode=None,
                 data_store='default', record_store='default',
                 on_changed='error', description='', data_label=None,
                 input_datastore=None):
        self.path = os.getcwd()
        if not os.path.exists(".smt"):
            os.mkdir(".smt")
        if os.path.exists(_get_project_file(self.path)):
            raise Exception("Sumatra project already exists in this directory.")
        self.name = name
        self.default_executable = default_executable
        self.default_repository = default_repository # maybe we should be storing the working copy instead, as this has a ref to the repository anyway
        self.default_main_file = default_main_file
        self.default_launch_mode = default_launch_mode
        if data_store == 'default':
            data_store = datastore.FileSystemDataStore(None)
        self.data_store = data_store # a data store object
        self.input_datastore = input_datastore or self.data_store
        if record_store == 'default':
            record_store = DefaultRecordStore(".smt/records")
        self.record_store = record_store
        self.on_changed = on_changed
        self.description = description
        self.data_label = data_label
        self._most_recent = None
        self.web_settings = {'nb_records_per_page':RECORDS_PER_PAGE}
        self.save()
        print "Sumatra project successfully set up"
    
    def __set_data_label(self, value):
        assert value in (None, 'parameters', 'cmdline')
        self._data_label = value
    def __get_data_label(self):
        return self._data_label
    data_label = property(fset=__set_data_label, fget=__get_data_label)
    
    def save(self):
        """Save state to some form of persistent storage. (file, database)."""
        state = {}
        for name in ('name', 'default_executable', 'default_repository',
                     'default_launch_mode', 'data_store', 'record_store',
                     'default_main_file', 'on_changed', 'description',
                     'data_label', '_most_recent', 'input_datastore', 'web_settings'):
            attr = getattr(self, name)
            if hasattr(attr, "__getstate__"):
                state[name] = {'type': attr.__class__.__module__ + "." + attr.__class__.__name__}
                for key, value in attr.__getstate__().items():
                    state[name][key] = value
            else:
                state[name] = attr
        f = open(_get_project_file(self.path), 'w') # should check if file exists?
        json.dump(state, f, indent=2)
        f.close()
    
    def info(self):
        """Show some basic information about the project."""
        template = """
        Sumatra project
        ---------------
        Name                : %(name)s
        Default executable  : %(default_executable)s
        Default repository  : %(default_repository)s
        Default main file   : %(default_main_file)s
        Default launch mode : %(default_launch_mode)s
        Data store (output) : %(data_store)s
        .          (input)  : %(input_datastore)s
        Record store        : %(record_store)s
        Code change policy  : %(on_changed)s
        Append label to     : %(_data_label)s
        """
        return _remove_left_margin(template % self.__dict__)
    
    def new_record(self, parameters={}, input_data=[], script_args="",
                   executable='default', repository='default',
                   main_file='default', version='latest', launch_mode='default',
                   label=None, reason=None):
        if executable == 'default':
            executable = deepcopy(self.default_executable)
        if repository == 'default':
            repository = deepcopy(self.default_repository)
        if main_file == 'default':
            main_file = self.default_main_file
        if launch_mode == 'default':
            launch_mode = deepcopy(self.default_launch_mode)
        working_copy = repository.get_working_copy()
        version, diff = self.update_code(working_copy, version)
        record = Record(executable, repository, main_file, version, launch_mode,
                        self.data_store, parameters, input_data, script_args, 
                        label=label, reason=reason, diff=diff,
                        on_changed=self.on_changed,
                        input_datastore=self.input_datastore)
        record.register(working_copy)
        return record
    
    def launch(self, parameters={}, input_data=[], script_args="",
               executable='default', repository='default', main_file='default',
               version='latest', launch_mode='default', label=None, reason=None):
        """Launch a new simulation or analysis."""
        record = self.new_record(parameters, input_data, script_args,
                                 executable, repository, main_file, version,
                                 launch_mode, label, reason)
        record.run(with_label=self.data_label)
        self.add_record(record)
        self.save()
        return record.label
    
    def update_code(self, working_copy, version='latest'):
        # Check if the working copy has modifications and prompt to commit or revert them
        # we really need to extend this to the dependencies, but we need to take extra special care that the
        # code ends up in the same condition as before the run
        diff = ''
        changed = working_copy.has_changed()
        if version == 'latest':
            if changed and self.on_changed == "error":
                raise UncommittedModificationsError("Code has changed, please commit your changes")
            working_copy.use_latest_version()
            version = working_copy.current_version()
            if changed and self.on_changed == "store-diff":
                diff = working_copy.diff()
        else:
            if changed:
                raise UncommittedModificationsError("Code has changed. These changes will be lost when switching to a different version, so please commit your changes and then retry.")
            working_copy.use_version(version) # what if there are local modifications and we're using store-diff? Do we store patches and then restore them?
        return version, diff
    
    def add_record(self, record):
        """Add a simulation or analysis record."""
        self.record_store.save(self.name, record)
        self._most_recent = record.label
    
    def get_record(self, label):
        """Search for a record with the supplied label and return it if found.
           Otherwise return None."""
        return self.record_store.get(self.name, label)
    
    def delete_record(self, label, delete_data=False):
        """Delete a record. Return 1 if the record is found.
           Otherwise return 0."""
        if delete_data:
            self.get_record(label).delete_data()
        self.record_store.delete(self.name, label)
        self._most_recent = self.record_store.most_recent(self.name)
    
    def delete_by_tag(self, tag, delete_data=False):
        """Delete all records with a given tag. Return the number of records deleted."""
        if delete_data:
            for record in self.record_store.list(self.name, tag):
                record.delete_data()
        n = self.record_store.delete_by_tag(self.name, tag)
        self._most_recent = self.record_store.most_recent(self.name)
        return n
    
    def format_records(self, format='text', mode='short', tags=None):
        records = self.record_store.list(self.name, tags)
        formatter = get_formatter(format)(records)
        return formatter.format(mode) 
    
    def most_recent(self):
        return self.get_record(self._most_recent)
    
    def add_comment(self, label, comment):
        try:
            record = self.record_store.get(self.name, label)
        except Exception, e:
            raise Exception("%s. label=<%s>" % (e,label))
        record.outcome = comment
        self.record_store.save(self.name, record)
        
    def add_tag(self, label, tag):
        record = self.record_store.get(self.name, label)
        record.tags.add(tag)
        self.record_store.save(self.name, record)
    
    def remove_tag(self, label, tag):
        record = self.record_store.get(self.name, label)
        record.tags.remove(tag)
        self.record_store.save(self.name, record)
    
    def compare(self, label1, label2, ignore_mimetypes=[], ignore_filenames=[]):
        record1 = self.record_store.get(self.name, label1)
        record2 = self.record_store.get(self.name, label2)
        return record1.difference(record2, ignore_mimetypes, ignore_filenames)        
    
    def show_diff(self, label1, label2, mode='short', ignore_mimetypes=[], ignore_filenames=[]):
        diff = self.compare(label1, label2, ignore_mimetypes, ignore_filenames)
        formatter = get_diff_formatter()(diff)
        return formatter.format(mode)


def _load_project_from_json(path):
    f = open(_get_project_file(path), 'r')
    data = json.load(f)
    f.close()
    prj = Project.__new__(Project)
    prj.path = path
    for key, value in data.items():
        if isinstance(value, dict) and "type" in value:
            parts = str(value["type"]).split(".") # make sure not unicode, see http://stackoverflow.com/questions/1971356/haystack-whoosh-index-generation-error/2683624#2683624
            module_name = ".".join(parts[:-1])
            class_name = parts[-1]
            _temp = __import__(module_name, globals(), locals(), [class_name], -1) # from <module_name> import <class_name>
            cls = getattr(_temp, class_name)
            args = {}
            for k,v in value.items():
                if k != 'type':
                    args[str(k)] = v # need to use str() as json module uses all unicode
            setattr(prj, key, cls(**args))
        else:
            setattr(prj, key, value)
    return prj

def _load_project_from_pickle(path):
    # earlier versions of Sumatra saved Projects using pickle
    f = open(_get_project_file(path), 'r')
    prj = pickle.load(f)
    f.close()
    return prj

def load_project(path=None):
    """
    Read project from directory passed as the argument and return Project
    object. If no argument is given, the project is read from the current
    directory.
    """
    if not path:
        p = os.getcwd()
    else:
        p = path
    while not os.path.isdir(os.path.join(p, ".smt")):
        oldp, p = p, os.path.dirname(p)
        if p == oldp:
            raise IOError("No Sumatra project exists in the current directory or above it.")
    mimetypes.init([os.path.join(p, ".smt", "mime.types")])
    #try:
    prj = _load_project_from_json(p)
    #except Exception:
    #    prj = _load_project_from_pickle(p)
    return prj
