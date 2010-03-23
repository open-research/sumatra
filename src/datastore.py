"""
The datastore module provides an abstraction layer around data storage,
allowing different methods of storing simulation results (local filesystem,
remote filesystem, database, etc.) to provide a common interface.

Currently, only local filesystem storage is supported.

Classes
-------

FileSystemDataStore - provides methods for accessing and archiving files stored
                      on a local file system, under a given root directory.
                      
Functions
---------

get_data_store() - return a DataStore object based on a class name and
                   constructor arguments.
"""

import os
import tarfile
import datetime
import shutil
import logging
import mimetypes
from subprocess import Popen

class DataStore(object):
    
    def get_state(self):
        """
        Since each subclass has different attributes, we provide this method
        as a standard way of obtaining these attributes, for database storage,
        etc. Returns a dict.
        """
        raise NotImplementedError


class FileSystemDataStore(DataStore):
    
    def __init__(self, root):
        self.root = root or "./Data"
        if not os.path.exists(self.root):
            os.mkdir(self.root)

    def __str__(self):
        return self.root
    
    def get_state(self):
        return {'root': self.root}
    
    def find_new_files(self, timestamp):
        """Finds newly created/changed files in dataroot."""
        # The timestamp-based approach creates problems when running several
        # simulations at once, since datafiles created by other simulations may
        # be mixed in with this one.
        # THIS NEEDS FIXED!
        timestamp = timestamp.replace(microsecond=0) # Round down to the nearest second
        # Find and add new data files
        length_dataroot = len(self.root) + len(os.path.sep)
        new_files = []
        for root, dirs, files in os.walk(self.root):
            #print root, dirs, files
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.join(root[length_dataroot:],file)
                last_modified = datetime.datetime.fromtimestamp(os.stat(full_path).st_mtime)
                if  last_modified >= timestamp:
                    new_files.append(relative_path)
        return new_files
    
    def archive(self, timestamp, label, key, delete_originals=False):
        """Archives files based on an access key, and deletes the originals."""
        data_archive = tarfile.open(label + ".tar.gz",'w:gz')
        logging.info("Archiving data to file %s" % data_archive.name)
        length_dataroot = len(self.root) + 1 # +1 for the "/"
        # Add parameter file
        parameter_file = os.path.join(os.getcwd(), label + ".param")
        if os.path.exists(parameter_file):
            data_archive.add(parameter_file, os.path.join(label, label + ".param"))
        # Find and add new data files
        new_files = self.find_new_files(timestamp)
        for file_path in new_files:
            archive_path = os.path.join(label, self.root[length_dataroot:], file_path)
            data_archive.add(os.path.join(self.root, file_path), archive_path)
        data_archive.close()
        # Move the archive to dataroot
        shutil.copy(data_archive.name, self.root) # shutil.move() doesn't work as expected if dataroot is a symbolic link
        os.remove(data_archive.name)
        # Delete original files.
        if delete_originals:
            if os.path.exists(parameter_file):
                os.remove(parameter_file)
            logging.debug("Deleting %s" % new_files)
            for file in new_files:
                os.remove(os.path.join(self.root, file))
                
    def list_files(self, key):
        return [DataFile(path, self) for path in key]
    
    def get_content(self, key, path, max_length=None):
        full_path = os.path.join(self.root, path)
        f = open(full_path, 'r')
        # check the file size. Truncate if necessary
        if max_length:
            content = f.read(max_length)
        else:
            content = f.read()
        f.close()
        return content
    
    
class DataFile(object):
    
    def __init__(self, path, store):
        self.path = path
        self.full_path = os.path.join(store.root, path)
        self.name = os.path.basename(self.full_path)
        self.extension = os.path.splitext(self.full_path)
        self.mimetype, self.encoding = mimetypes.guess_type(self.full_path)
        stats = os.stat(self.full_path)
        self.size = stats.st_size
        
    def __str__(self):
        return self.path
    
    @property
    def content(self):
        f = open(self.full_path, 'r')
        content = f.read()
        f.close()
        return content
    
    @property
    def sorted_content(self):
        sorted_path = "%s,sorted" % self.full_path
        if not os.path.exists(sorted_path):
            cmd = "sort %s > %s" % (self.full_path, sorted_path)
            job = Popen(cmd, shell=True)
            job.wait()
        f = open(sorted_path, 'r')
        content = f.read()
        f.close()
        if len(content) != self.size: # sort adds a \n if the file does not end with one
            assert len(content) == self.size + 1
            content = content[:-1]
        return content
        
    def __eq__(self, other):
        if self.size != other.size:
            return False
        elif self.content == other.content:
            return True
        else:
            return self.sorted_content == other.sorted_content
        
    def __ne__(self, other):
        return not self.__eq__(other)
        
    
def get_data_store(type, parameters):
    cls = eval(type)
    return cls(**parameters)
