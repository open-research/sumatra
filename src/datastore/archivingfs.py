"""
Datastore based on files written to the local filesystem, archived in gzipped
tar files, then retrieved from the tar files.
"""

from __future__ import with_statement
import os
import tarfile
import shutil
import logging
import mimetypes


from base import DataItem, DataKey
from filesystem import FileSystemDataStore


class ArchivedDataFile(DataItem):
    """A file-like object, that represents a file inside a tar archive"""
    # current implementation just for real files
    
    def __init__(self, path, store):
        self.path = path
        archive_label = self.path.split("/")[0]
        self.tarfile_path = os.path.join(store.archive_store, archive_label + ".tar.gz")
        self.size = self._get_info().size
        self.name = os.path.basename(self.path)
        self.extension = os.path.splitext(self.name)
        self.mimetype, self.encoding = mimetypes.guess_type(self.path)

    def _get_info(self):
        with tarfile.open(self.tarfile_path, 'r') as data_archive:
            info = data_archive.getmember(self.path)
        return info
    
    def get_content(self, max_length=None):
        with tarfile.open(self.tarfile_path, 'r') as data_archive:
            f = data_archive.extractfile(self.path)
            if max_length:
                content = f.read(max_length)
            else:
                content = f.read()
            f.close()
            return content
    content = property(fget=get_content)
    
    @property
    def sorted_content(self):
        raise NotImplementedError


class ArchivingFileSystemDataStore(FileSystemDataStore):
    """
    Represents a locally-mounted filesystem that archives any new files created
    in it. The root of the data store will generally be a subdirectory of the
    real filesystem.
    """
    data_item_class = ArchivedDataFile
    
    def __init__(self, root, archive=".smt/archive"):
        self.root = root or "./Data"
        self.archive_store = archive
        if not os.path.exists(self.archive_store):
            os.mkdir(self.archive_store)
    
    def __getstate__(self):
        return {'root': self.root, 'archive': self.archive_store}
    
    def find_new_data(self, timestamp):
        """Finds newly created/changed data items"""
        new_files = self._find_new_data_files(timestamp)
        label = timestamp.strftime("%Y%m%d-%H%m%S")
        archive_paths = self._archive(label, new_files)
        return [ArchivedDataFile(path, self).generate_key()
                for path in archive_paths]
    
    def _archive(self, label, files, delete_originals=True):
        """
        Archives files and, by default, deletes the originals.
        """
        tf = tarfile.open(label + ".tar.gz",'w:gz')
        logging.info("Archiving data to file %s" % tf.name)
        # Add data files
        archive_paths = []
        for file_path in files:
            archive_path = os.path.join(label, file_path)
            tf.add(os.path.join(self.root, file_path), archive_path)
            archive_paths.append(archive_path)
        tf.close()
        # Move the archive to self.archive_store
        shutil.copy(tf.name, self.archive_store) # shutil.move() doesn't work as expected if dataroot is a symbolic link
        os.remove(tf.name)
        # Delete original files.
        if delete_originals:
            for file_path in files:
                os.remove(os.path.join(self.root, file_path))
        self._last_label = label # useful for testing
        return archive_paths
    
    def delete(self, *keys):
        """Delete the files corresponding to the given keys."""
        raise NotImplementedError("Deletion of individual files not supported.")

    def contains_path(self, path):
        raise NotImplementedError
