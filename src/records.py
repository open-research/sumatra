"""
The records module defines the Record class, which gathers and stores
information about an individual simulation or analysis run.

Classes
-------

Record - gathers and stores information about an individual simulation or
         analysis run.
         Can be instantiated directly, but more usually created by the
         new_record() method of Project.
"""

from datetime import datetime
import time
import os
import re
import getpass
from operator import or_
from formatting import get_formatter
import dependency_finder

def assert_equal(a, b, msg=''):
    assert a == b, "%s: %s %s != %s %s" % (msg, a, type(a), b, type(b))

class Record(object):
    """
    
    """
    
    def __init__(self, executable, repository, main_file, version, launch_mode,
                 datastore, parameters={}, input_data=[], script_arguments="",
                 label=None, reason=None, diff='', user='', on_changed='error',
                 input_datastore=None, stdout_stderr='Not launched.'):
        self.timestamp = datetime.now() # might need to allow for this to be set as argument to allow for distributed/batch simulations on machines with out-of-sync clocks
        self.label = label or self.timestamp.strftime("%Y%m%d-%H%M%S")
        assert len(self.label) > 0
        self.reason = reason
        self.duration = None
        self.executable = executable # an Executable object incorporating path, version, maybe system information
        self.repository = repository # a Repository object
        self.main_file = main_file
        self.version = version
        self.parameters = parameters
        self.input_data = input_data # a list containing DataKey objects
        self.script_arguments = script_arguments
        self.launch_mode = launch_mode # a LaunchMode object - basically, run serially or with MPI. If MPI, what configuration
        self.datastore = datastore.copy()
        self.input_datastore = input_datastore or self.datastore
        self.outcome = None
        self.output_data = []
        self.tags = set()
        self.diff = diff
        self.user = user
        self.on_changed = on_changed
        self.stdout_stderr = stdout_stderr
    
    def register(self, working_copy):
        """Record information about the environment."""
        # Check the code hasn't changed and the version is correct
        if len(self.diff) == 0:
            assert not working_copy.has_changed()
        assert_equal(working_copy.current_version(), self.version, "version")
        # Record dependencies
        if len(self.main_file.split()) == 1: # this assumes filenames cannot contain spaces
            self.dependencies = dependency_finder.find_dependencies(self.main_file, self.executable)
        else: # if self.main_file contains multiple file names
            # this seems a bit hacky. Should perhaps store a list self.main_files, _and_ check that all files exist.
            self.dependencies = []
            for main_file in self.main_file.split():
                self.dependencies.extend(dependency_finder.find_dependencies(main_file, self.executable))
        # if self.on_changed is 'error', should check that all the dependencies have empty diffs and raise an UncommittedChangesError otherwise
        # Record platform information
        self.platforms = self.launch_mode.get_platform_information()
    
    def run(self, with_label=False):
        """
        Launch the simulation or analysis.
        
        with_label - adds the record label either to the parameter file
                     (with_label="parameters") or to the end of the command
                     line (with_label="cmdline"), and appends the label to the
                     datastore root. This allows the program being run to
                     create files in a directory specific to this run.
        """
        data_label = None
        if with_label:
            if with_label == 'parameters':
                self.parameters.update({"sumatra_label": self.label})
            elif with_label == 'cmdline':
                data_label = self.label
            else:
                raise Exception("with_label must be either 'parameters' or 'cmdline'")
            self.datastore.root  = os.path.join(self.datastore.root, self.label)
        # run pre-simulation/analysis tasks, e.g. nrnivmodl
        self.launch_mode.pre_run(self.executable)
        # Write the executable-specific parameter file
        script_arguments = self.script_arguments
        if self.parameters:
            parameter_file = "%s.param" % self.label.replace("/", "_")
            self.executable.write_parameters(self.parameters, parameter_file)
            script_arguments = script_arguments.replace("<parameters>", parameter_file)
        # Run simulation/analysis
        start_time = time.time()
        result = self.launch_mode.run(self.executable, self.main_file,
                                      script_arguments, data_label)
        self.duration = time.time() - start_time

        # try to get stdout_stderr from lauch_mode
        try:
            if self.launch_mode.stdout_stderr not in (None,""):
                self.stdout_stderr = self.launch_mode.stdout_stderr
            else:
                self.stdout_stderr = "No output."
        except:
            self.stdout_stderr = "Not available."
        
        # Run post-processing scripts
        pass # skip this if there is an error
        # Search for newly-created datafiles
        if self.parameters and os.path.exists(parameter_file):
            os.remove(parameter_file)
        self.output_data = self.datastore.find_new_data(self.timestamp)
        if self.output_data:
            print "Data keys are", self.output_data
        else:
            print "No data produced."
    
    def __repr__(self):
        return "Record #%s" % self.label
    
    def describe(self, format='text', mode='long'):
        formatter = get_formatter(format)([self])
        return formatter.format(mode)
    
    def __ne__(self, other):
        return bool(self.difference(other))
    
    def __eq__(self, other):
        return not self.__ne__(other)
    
    def difference(self, other_record, ignore_mimetypes=[], ignore_filenames=[]):
        """
        Determine the difference between this computational experiment and
        another (code, platform, results, etc.).
        
        Return a RecordDifference object.
        """
        return RecordDifference(self, other_record, ignore_mimetypes, ignore_filenames)
    
    def delete_data(self):
        """
        Delete any data files associated with this record.
        """
        self.datastore.delete(*self.output_data)
        self.output_data = []


class RecordDifference(object):
    """Represents the difference between two Record objects."""
    
    ignore_mimetypes = [r'image/\w+', r'video/\w+']
    ignore_filenames = [r'\.log', r'^log']
    
    def __init__(self, recordA, recordB,
                 ignore_mimetypes=[],
                 ignore_filenames=[]):
        self.recordA = recordA
        self.recordB = recordB
        assert not isinstance(ignore_mimetypes, basestring) # catch a 
        assert not isinstance(ignore_filenames, basestring) # common error
        self.ignore_mimetypes += ignore_mimetypes
        self.ignore_filenames += ignore_filenames
        self.executable_differs = recordA.executable != recordB.executable
        self.repository_differs = recordA.repository != recordB.repository
        self.main_file_differs = recordA.main_file != recordB.main_file
        self.version_differs = recordA.version != recordB.version
        for rec in recordA, recordB:
            if rec.parameters:
                rec.parameters.pop("sumatra_label", 1)
        self.parameters_differ = recordA.parameters != recordB.parameters
        self.input_data_differ = recordA.input_data != recordB.input_data  # now that input_data is a list of DataKeys, need to make this a property, like data_differ
        self.script_arguments_differ = recordA.script_arguments != recordB.script_arguments
        self.launch_mode_differs = recordA.launch_mode != recordB.launch_mode
        #self.platforms
        #self.datastore = datastore
        #self.output_data = None
        self.diff_differs = recordA.diff != recordB.diff
    
    def __nonzero__(self):
        """
        Return True if there are differences in executable, code, parameters or
        output data between the records, otherwise return False.
        
        Differences in launch mode or platform are not counted, since those
        don't in principle make it a different experiment (they may do in
        practice, but then the output data will be different).
        """
        return reduce(or_, (self.executable_differs, self.code_differs,
                            self.input_data_differ, self.script_arguments_differ,
                            self.parameters_differ, self.data_differs))
    
    def __repr__(self):
        s = "RecordDifference(%s, %s):" % (self.recordA.label, self.recordB.label)
        if self.executable_differs:
            s += 'X'
        if self.code_differs:
            s += 'C'
        if self.parameters_differ:
            s += 'P'
        if self.data_differs:
            s += 'D'
        if self.input_data_differ:
            s += 'I'
        if self.script_arguments_differ:
            s += 'S'
        return s
    
    @property
    def code_differs(self):
        return reduce(or_, (self.repository_differs, self.main_file_differs,
                            self.version_differs, self.diff_differs,
                            self.dependencies_differ))
    
    @property
    def dependencies_differ(self):
        return set(self.recordA.dependencies) != set(self.recordB.dependencies)
    
    @property
    def dependency_differences(self):
        depsA = {}
        for dep in self.recordA.dependencies:
            depsA[dep.name] = dep
        depsB = {}
        for dep in self.recordB.dependencies:
            depsB[dep.name] = dep
        diffs = {}
        for name in depsA:
            if name in depsB:
                if depsA[name] != depsB[name]:
                    diffs[name] = (depsA[name], depsB[name])
            else:
                diffs[name] = (depsA[name], None)
        for name in depsB:
            if name not in depsA:
                diffs[name] = (None, depsB[name])
        return diffs
    
    def _list_datakeys(self):
        keys = {self.recordA.label: {}, self.recordB.label: {}}
        for rec in self.recordA, self.recordB:
            for key in rec.output_data:
                ignore = False
                name = os.path.basename(key.path)
                if key.metadata['mimetype']:
                    for pattern in self.ignore_mimetypes:
                        if re.match(pattern, key.metadata['mimetype']):
                            ignore = True
                            break
                for pattern in self.ignore_filenames:
                    if re.search(pattern, name):
                        ignore = True
                        break
                if not ignore:
                    keys[rec.label][name] = key
        return keys
                    
    @property
    def data_differs(self):  # rename to "output_data_differs"
        keys = self._list_datakeys()
        filenamesA = set(keys[self.recordA.label].keys())
        filenamesB = set(keys[self.recordB.label].keys())
        if len(filenamesA) == len(filenamesB) == 0:
            return False
        if filenamesA.difference(filenamesB):
            return True
        differs = {}
        for filename in filenamesA:
            differs[filename] = keys[self.recordA.label][filename].digest != keys[self.recordB.label][filename].digest # doesn't account for same-after-sorting
        return reduce(or_, differs.values())
        
    @property
    def data_differences(self): # rename to "output_data_differences"
        keys = self._list_datakeys()
        A = keys[self.recordA.label]
        B = keys[self.recordB.label]
        diffs = {}
        for name in A:
            if name in B:
                if A[name].digest != B[name].digest:
                    diffs[name] = (A[name], B[name])
            else:
                diffs[name] = (A[name], None)
        for name in B:
            if name not in B:
                diffs[name] = (None, B[name])
        return diffs
    
    @property
    def launch_mode_differences(self):
        if self.launch_mode_differs:
            return self.recordA.launch_mode, self.recordB.launch_mode
        else:
            return None
        
