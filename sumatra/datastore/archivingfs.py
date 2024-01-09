"""
Datastore based on files written to the local filesystem, archived in gzipped
tar files, then retrieved from the tar files.


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import os
import tarfile
import shutil
import logging
import mimetypes
import datetime
from contextlib import closing
from sumatra.core import TIMESTAMP_FORMAT, component


from .base import DataItem
from .filesystem import FileSystemDataStore


class ArchivedDataFile(DataItem):
    """A file-like object, that represents a file inside a tar archive"""
    # current implementation just for real files

    def __init__(self, path, store, creation=None):
        self.path = path
        archive_label = self.path.split(os.path.sep)[0]
        self.tarfile_path = os.path.join(store.archive_store, archive_label + ".tar.gz")
        info = self._get_info()
        self.size = info.size
        self.creation = creation or datetime.datetime.fromtimestamp(info.mtime).replace(microsecond=0)
        self.name = os.path.basename(self.path)
        self.extension = os.path.splitext(self.name)
        self.mimetype, self.encoding = mimetypes.guess_type(self.path)

    def _get_info(self):
        with closing(tarfile.open(self.tarfile_path, 'r')) as data_archive:
            info = data_archive.getmember(self.path)
        return info

    def get_content(self, max_length=None):
        with closing(tarfile.open(self.tarfile_path, 'r')) as data_archive:
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


@component
class ArchivingFileSystemDataStore(FileSystemDataStore):
    """
    Represents a locally-mounted filesystem that archives any new files created
    in it. The root of the data store will generally be a subdirectory of the
    real filesystem.
    """
    data_item_class = ArchivedDataFile

    def __init__(self, root, archive=".smt/archive"):
        super(ArchivingFileSystemDataStore, self).__init__(root)
        self.archive_store = archive
        # should allow specification of archive format, e.g. tar.gz or zip

    def __str__(self):
        return "{0} (archiving to {1})".format(self.root, self.archive_store)

    def __getstate__(self):
        return {'root': self.root, 'archive': self.archive_store}

    def find_new_data(self, timestamp):
        """Finds newly created/changed data items"""
        new_files = self._find_new_data_files(timestamp)
        label = timestamp.strftime(TIMESTAMP_FORMAT)
        archive_paths = self._archive(label, new_files)
        return [ArchivedDataFile(path, self).generate_key()
                for path in archive_paths]

    def _archive(self, label, files, delete_originals=True):
        """
        Archives files and, by default, deletes the originals.
        """
        if not os.path.exists(self.archive_store):
            os.mkdir(self.archive_store)
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
