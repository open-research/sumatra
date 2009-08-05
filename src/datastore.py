import os
import tarfile
import datetime
import shutil

class FileSystemDataStore(object):
    
    def __init__(self, root):
        self.root = root or "./Data"
        if not os.path.exists(self.root):
            os.mkdir(self.root)

    def __str__(self):
        return self.root
    
    def archive(self, timestamp, label):
        """Finds newly created/changed files in dataroot."""
        # The timestamp-based approach creates problems when running several
        # simulations at once, since datafiles created by other simulations may
        # be archived with this one.
        # THIS NEEDS FIXED!
        timestamp = timestamp.replace(microsecond=0) # Round down to the nearest second
        data_archive = tarfile.open(label + ".tar.gz",'w:gz')
        print "Archiving data to file", data_archive.name
        length_dataroot = len(self.root) + 1 # +1 for the "/"
        # Add parameter file
        data_archive.add(os.path.join(os.getcwd(),label + ".param"),os.path.join(label,label + ".param"))
        # Find and add new data files
        new_files = []; new_dirs = []
        for root, dirs, files in os.walk(self.root):
            print root, dirs, files
            for file in files:
                abspath = os.path.join(root,file)
                relpath = os.path.join(label,root[length_dataroot:],file)
                last_modified = datetime.datetime.fromtimestamp(os.stat(abspath).st_mtime)
                if  last_modified >= timestamp:
                    data_archive.add(abspath,relpath)
                    new_files.append(abspath)
            for dir in dirs:
                abspath = os.path.join(root,dir)
                last_modified = datetime.datetime.fromtimestamp(os.stat(abspath).st_mtime)
                if  last_modified >= timestamp:
                    new_dirs.append(abspath)
        data_archive.close()
        # Move the archive to dataroot
        shutil.copy(data_archive.name, self.root) # shutil.move() doesn't work as expected if dataroot is a symbolic link
        os.remove(data_archive.name)
        # Delete original files.
        os.remove(label + ".param")
        print "Deleting", new_files
        for file in new_files:
            os.remove(file)
        for dir in new_dirs:
            try:
                shutil.rmtree(dir)
            except OSError:
                pass