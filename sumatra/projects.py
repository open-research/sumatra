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
import re
try:
    import cPickle as pickle
except ImportError:
    import pickle
from copy import deepcopy
import uuid
import sumatra
from sumatra.records import Record
from sumatra import programs, datastore
from sumatra.formatting import get_formatter, get_diff_formatter
from sumatra.recordstore import DefaultRecordStore
from sumatra.versioncontrol import UncommittedModificationsError, get_working_copy, VersionControlError
from sumatra.core import TIMESTAMP_FORMAT
import mimetypes
try:
    import json
except ImportError:
    import simplejson as json
import logging

logger = logging.getLogger("Sumatra")

DEFAULT_PROJECT_FILE = "project"

LABEL_GENERATORS = {
    'timestamp': lambda: None, # this is the default, implemented in the Record class
    'uuid': lambda: str(uuid.uuid4()).split('-')[-1]
}


def _remove_left_margin(s): # replace this by textwrap.dedent?
    lines = s.strip().split('\n')
    return "\n".join(line.strip() for line in lines)

def _get_project_file(path):
    return os.path.join(path, ".smt", DEFAULT_PROJECT_FILE)


class Project(object):
    valid_name_pattern = r'(?P<project>\w+[\w\- ]*)'

    def __init__(self, name, default_executable=None, default_repository=None,
                 default_main_file=None, default_launch_mode=None,
                 data_store='default', record_store='default',
                 on_changed='error', description='', data_label=None,
                 input_datastore=None, label_generator='timestamp',
                 timestamp_format=TIMESTAMP_FORMAT,
                 allow_command_line_parameters=True):
        self.path = os.getcwd()
        if not os.path.exists(".smt"):
            os.mkdir(".smt")
        if os.path.exists(_get_project_file(self.path)):
            raise Exception("Sumatra project already exists in this directory.")
        if re.match(Project.valid_name_pattern, name):
            self.name = name
        else:
            raise ValueError("Invalid project name. Names may only contain letters, numbers, spaces and hyphens")
        self.default_executable = default_executable
        self.default_repository = default_repository # maybe we should be storing the working copy instead, as this has a ref to the repository anyway
        self.default_main_file = default_main_file
        self.default_launch_mode = default_launch_mode
        if data_store == 'default':
            data_store = datastore.FileSystemDataStore(None)
        self.data_store = data_store # a data store object
        self.input_datastore = input_datastore or self.data_store
        if record_store == 'default':
            record_store = DefaultRecordStore(os.path.abspath(".smt/records"))
        self.record_store = record_store
        self.on_changed = on_changed
        self.description = description
        self.data_label = data_label
        self.label_generator = label_generator
        self.timestamp_format = timestamp_format        
        self.sumatra_version = sumatra.__version__
        self.allow_command_line_parameters = allow_command_line_parameters
        self._most_recent = None            
        self.save()
        print("Sumatra project successfully set up")
        
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
                     'data_label', '_most_recent', 'input_datastore',
                     'label_generator', 'timestamp_format', 'sumatra_version',
                     'allow_command_line_parameters'):
            attr = getattr(self, name, None)
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
        Project name        : %(name)s
        Default executable  : %(default_executable)s
        Default repository  : %(default_repository)s
        Default main file   : %(default_main_file)s
        Default launch mode : %(default_launch_mode)s
        Data store (output) : %(data_store)s
        .          (input)  : %(input_datastore)s
        Record store        : %(record_store)s
        Code change policy  : %(on_changed)s
        Append label to     : %(_data_label)s
        Label generator     : %(label_generator)s
        Timestamp format    : %(timestamp_format)s
        Sumatra version     : %(sumatra_version)s
        """
        return _remove_left_margin(template % self.__dict__)
    
    def new_record(self, parameters={}, input_data=[], script_args="",
                   executable='default', repository='default',
                   main_file='default', version='current', launch_mode='default',
                   label=None, reason=None, timestamp_format='default'):
        logger.debug("Creating new record")
        if executable == 'default':
            executable = deepcopy(self.default_executable)           
        if repository == 'default':
            repository = deepcopy(self.default_repository)
        if main_file == 'default':
            main_file = self.default_main_file
        if launch_mode == 'default':
            launch_mode = deepcopy(self.default_launch_mode)
        if timestamp_format == 'default':
            timestamp_format = self.timestamp_format
        working_copy = repository.get_working_copy()
        version, diff = self.update_code(working_copy, version)
        if label is None:
            label = LABEL_GENERATORS[self.label_generator]()
        record = Record(executable, repository, main_file, version, launch_mode,
                        self.data_store, parameters, input_data, script_args, 
                        label=label, reason=reason, diff=diff,
                        on_changed=self.on_changed,
                        input_datastore=self.input_datastore,
                        timestamp_format=timestamp_format)
        if not isinstance(executable, programs.MatlabExecutable):
            record.register(working_copy)
        return record
    
    def launch(self, parameters={}, input_data=[], script_args="",
               executable='default', repository='default', main_file='default',
               version='current', launch_mode='default', label=None, reason=None, 
               timestamp_format='default', repeats=None):
        """Launch a new simulation or analysis."""
        record = self.new_record(parameters, input_data, script_args,
                                 executable, repository, main_file, version,
                                 launch_mode, label, reason, timestamp_format) 
        record.run(with_label=self.data_label)
        if 'matlab' in record.executable.name.lower():
            record.register(record.repository.get_working_copy())
        if repeats:
            record.repeats = repeats
        self.add_record(record)
        self.save()
        return record.label
    
    def update_code(self, working_copy, version='current'):
        """Check if the working copy has modifications and prompt to commit or revert them."""
        # we really need to extend this to the dependencies, but we need to take extra special care that the
        # code ends up in the same condition as before the run
        logger.debug("Updating working copy to use version: %s" % version)
        diff = ''
        changed = working_copy.has_changed()
        if version == 'current' or version == working_copy.current_version:
            if changed:
                if self.on_changed == "error":
                    raise UncommittedModificationsError("Code has changed, please commit your changes")    
                elif self.on_changed == "store-diff":
                    diff = working_copy.diff()
                else:
                    raise ValueError("store-diff must be either 'error' or 'store-diff'")
        elif changed:
            raise UncommittedModificationsError(
                "Code has changed. These changes will be lost when switching "
                "to a different version, so please commit or stash your "
                "changes and then retry.")
        elif version == 'latest':
            working_copy.use_latest_version()
        else:
            working_copy.use_version(version)
        version = working_copy.current_version()
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
    
    def format_records(self, format='text', mode='short', tags=None, reverse=False):
        records = self.record_store.list(self.name, tags)
        if reverse:
            records.reverse()
        formatter = get_formatter(format)(records, project=self, tags=tags)
        return formatter.format(mode) 

    def most_recent(self):
        try:
            return self.get_record(self._most_recent)
        except KeyError:  # the record pointed to by self._most_recent has been deleted
            self._most_recent = self.record_store.most_recent(self.name)
            return self.most_recent()

    def add_comment(self, label, comment):
        try:
            record = self.record_store.get(self.name, label)
        except Exception as e:
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

    def export(self):
        # copy the project data
        import shutil
        shutil.copy(".smt/project", ".smt/project_export.json")
        # export the record data
        f = open(".smt/records_export.json", 'w')
        f.write(self.record_store.export(self.name))
        f.close()
    
    def repeat(self, original_label, new_label=None):
        if original_label == 'last':
            tmp = self.most_recent()
        else:
            tmp = self.get_record(original_label)
        original = deepcopy(tmp)
        if hasattr(tmp.parameters, '_url'): # for some reason, _url is not copied.
            original.parameters._url = tmp.parameters._url # this is a hackish solution - needs fixed properly
        try:
            working_copy = get_working_copy()
        except VersionControlError:
            original.repository.checkout()
            working_copy = original.repository.get_working_copy()
        if working_copy.repository != original.repository:
            raise NotImplementedError("Ability to switch repositories not yet implemented.")
        current_version = working_copy.current_version()
        new_label = self.launch(parameters=original.parameters,
                                input_data=original.input_data,
                                script_args=original.script_arguments,
                                executable=original.executable,
                                main_file=original.main_file,
                                repository=original.repository,
                                version=original.version,
                                launch_mode=original.launch_mode,
                                label=new_label,
                                reason="Repeat experiment %s" % original.label,
                                repeats=original.label)
        working_copy.use_version(current_version)  # ensure we switch back to the original working copy state
        return new_label, original.label

    def backup(self):
        """        
        Create a new backup directory in the same location as the
        project directory and copy the contents of the project
        directory into the backup directory. Uses `_get_project_file`
        to extract the path to the project directory.
        
        :return:
          - `backup_dir`: the directory used for the backup

        """
        import shutil
        from datetime import datetime
        smt_dir = os.path.split(_get_project_file(self.path))[0]
        backup_dir = smt_dir + "_backup_%s" % datetime.now().strftime(TIMESTAMP_FORMAT)    
        shutil.copytree(smt_dir, backup_dir)
        return backup_dir

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
