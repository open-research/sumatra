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
    
    def __init__(self, executable, repository, main_file, version, parameters,
                 launch_mode, datastore, label=None, reason=None, diff='',
                 user='', on_changed='error'):
        self.timestamp = datetime.now() # might need to allow for this to be set as argument to allow for distributed/batch simulations on machines with out-of-sync clocks
        self.label = label or self.timestamp.strftime("%Y%m%d-%H%M%S")
        assert len(self.label) > 0
        self.reason = reason
        self.duration = None
        self.executable = executable # an Executable object incorporating path, version, maybe system information
        self.repository = repository # a Repository object
        self.main_file = main_file
        self.version = version
        self.parameters = parameters # a ParameterSet object
        self.launch_mode = launch_mode # a LaunchMode object - basically, run serially or with MPI. If MPI, what configuration
        self.datastore = datastore.copy()
        self.outcome = None
        self.data_key = None
        self.tags = set()
        self.diff = diff
        self.user = user
        self.on_changed = on_changed  
    
    def register(self):
        """Record information about the environment."""
        # Check the code hasn't changed and the version is correct
        if len(self.diff) == 0:
            assert not self.repository.working_copy.has_changed()
        assert_equal(self.repository.working_copy.current_version(), self.version, "version")
        # Record dependencies
        self.dependencies = dependency_finder.find_dependencies(self.main_file, self.executable, self.on_changed)
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
        print "datastore.root = ", self.datastore.root
        # run pre-simulation/analysis tasks, e.g. nrnivmodl
        self.launch_mode.pre_run(self.executable)
        # Write the executable-specific parameter file
        parameter_file = "%s.param" % self.label.replace("/", "_")
        self.executable.write_parameters(self.parameters, parameter_file)
        # Run simulation/analysis
        start_time = time.time()
        result = self.launch_mode.run(self.executable, self.main_file, parameter_file, data_label)
        self.duration = time.time() - start_time
        # Run post-processing scripts
        pass # skip this if there is an error
        # Search for newly-created datafiles
        self.data_key = self.datastore.find_new_files(self.timestamp)
        print "Data key is", self.data_key
        if os.path.exists(parameter_file):
            os.remove(parameter_file)
    
    def describe(self, format='text', mode='long'):
        formatter = get_formatter(format)([self])
        return formatter.format(mode)
    
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
        self.datastore.delete(self.data_key)
        self.data_key = self.datastore.empty_key
         

class RecordDifference(object):
    """Represents the difference between two Record objects."""
    
    ignore_mimetypes = [r'image/\w+', r'video/\w+']
    ignore_filenames = [r'\.log', r'^log']
    
    def __init__(self, recordA, recordB,
                 ignore_mimetypes=[],
                 ignore_filenames=[]):
        assert recordA.label != recordB.label
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
            rec.parameters.pop("sumatra_label", None)
        self.parameters_differ = recordA.parameters != recordB.parameters
        self.launch_mode_differs = recordA.launch_mode != recordB.launch_mode
        #self.platforms
        #self.datastore = datastore
        #self.data_key = None
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
                            self.parameters_differ, self.data_differs))
    
    @property
    def code_differs(self):
        return reduce(or_, (self.repository_differs, self.main_file_differs,
                            self.version_differs, self.diff_differs,
                            self.dependencies_differ))
    
    @property
    def dependencies_differ(self):
        if len(self.recordA.dependencies) != len(self.recordB.dependencies):
            return True
        for depA,depB in zip(self.recordA.dependencies, self.recordB.dependencies):
            if depA != depB:
                return True
        return False
    
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
    
    def _list_datafiles(self):
        files = {self.recordA.label: {}, self.recordB.label: {}}
        for rec in self.recordA, self.recordB:
            for file in rec.datastore.list_files(rec.data_key):
                ignore = False
                if file.mimetype:
                    for pattern in self.ignore_mimetypes:
                        if re.match(pattern, file.mimetype):
                            ignore = True
                            break
                for pattern in self.ignore_filenames:
                    if re.search(pattern, file.name):
                        ignore = True
                        break
                if not ignore:
                    files[rec.label][file.name] = file
        return files
                    
    @property
    def data_differs(self):
        files = self._list_datafiles()
        filenamesA = set(files[self.recordA.label].keys())
        filenamesB = set(files[self.recordB.label].keys())
        if len(filenamesA) == len(filenamesB) == 0:
            return False
        if filenamesA.difference(filenamesB):
            return True
        differs = {}
        for filename in filenamesA:
            differs[filename] = files[self.recordA.label][filename] != files[self.recordB.label][filename]
        return reduce(or_, differs.values())
        
    @property
    def data_differences(self):
        files = self._list_datafiles()
        A = files[self.recordA.label]
        B = files[self.recordB.label]
        diffs = {}
        for name in A:
            if name in B:
                if A[name] != B[name]:
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
        