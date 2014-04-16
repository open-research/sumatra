"""
Datastore based on files written to the local filesystem, that are then made
available at some URL.

The datastore itself does not take care of the mirroring, it is up to the
user to take care of this.
"""

import logging
import os
import mimetypes
from ..compatibility import urlopen
from .base import DataItem, DataKey
from .filesystem import FileSystemDataStore, DataFile


class MirroredDataFile(DataItem):
    """
    A file-like object, that represents a file existing both on a local
    file system and on a webserver.
    """

    def __init__(self, path, store):
        self.path = path
        self.full_path = os.path.join(store.root, path)
        if os.path.exists(self.full_path):
            stats = os.stat(self.full_path)
            self.size = stats.st_size
        else:
            self.size = -1
        self.name = os.path.basename(self.full_path)
        self.extension = os.path.splitext(self.full_path)
        self.mimetype, self.encoding = mimetypes.guess_type(self.full_path)
        self.url = store.mirror_base_url + self.path

    def get_content(self, max_length=None):
        if os.path.exists(self.full_path):  # first try to access local version
            f = open(self.full_path, 'rb')
        else:  # otherwise try the mirrored version
            f = urlopen(self.url)
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


class MirroredFileSystemDataStore(FileSystemDataStore):
    """
    Represents a locally-mounted filesystem whose contents are mirrored on
    a webserver, so that the files can be accessed via an HTTP URL.
    """
    data_item_class = MirroredDataFile

    def __init__(self, root, mirror_base_url):
        """
        root is the path on the local filesystem within which to search for
          new files
        mirror_base_url is a URL to which the file path should be appended
        """
        super(MirroredFileSystemDataStore, self).__init__(root)
        self.mirror_base_url = mirror_base_url

    def __getstate__(self):
        return {'root': self.root, 'mirror_base_url': self.mirror_base_url}

    def find_new_data(self, timestamp):
        """Finds newly created/changed data items"""
        new_files = self._find_new_data_files(timestamp)
        return [MirroredDataFile(path, self).generate_key()
                for path in new_files]

    def delete(self, *keys):
        """Delete the files corresponding to the given keys."""
        raise NotImplementedError("Deletion of individual files not supported.")

    def contains_path(self, path):
        raise NotImplementedError
