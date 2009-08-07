import os
import tarfile
import datetime
import shutil
import logging

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
        new_files = []
        for root, dirs, files in os.walk(self.root):
            #print root, dirs, files
            for file in files:
                file_path = os.path.join(root, file)
                last_modified = datetime.datetime.fromtimestamp(os.stat(file_path).st_mtime)
                if  last_modified >= timestamp:
                    new_files.append(file_path)
        return new_files
    
    def archive(self, label, key, delete_originals=False):
        """Archives files based on an access key, and deletes the originals."""
        data_archive = tarfile.open(label + ".tar.gz",'w:gz')
        logging.info("Archiving data to file %s" % data_archive.name)
        length_dataroot = len(self.root) + 1 # +1 for the "/"
        # Add parameter file
        data_archive.add(os.path.join(os.getcwd(),label + ".param"), os.path.join(label,label + ".param"))
        # Find and add new data files
        new_files = self.find_new_files()
        for file_path in new_files:
            archive_path = os.path.join(label,root[length_dataroot:],file)
            data_archive.add(file_path, archive_path)
        data_archive.close()
        # Move the archive to dataroot
        shutil.copy(data_archive.name, self.root) # shutil.move() doesn't work as expected if dataroot is a symbolic link
        os.remove(data_archive.name)
        # Delete original files.
        if delete_originals:
            os.remove(label + ".param")
            logging.debug("Deleting %s" % new_files)
            for file in new_files:
                os.remove(file)
                