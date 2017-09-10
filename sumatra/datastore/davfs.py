'''
Datastore via remote webdav connection
'''
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

import os
import tarfile
import logging
from fs.contrib.davfs import DAVFS
from urllib.parse import urlparse
from contextlib import closing

from sumatra.core import component
from .archivingfs import ArchivingFileSystemDataStore, ArchivedDataFile, TIMESTAMP_FORMAT


class DavFsDataItem(ArchivedDataFile):
    """Base class for data item classes, that may represent files or database records."""

    def __init__(self, path, store):
        # needs to be first cause _get_info is called in Base __init__
        self.store = store
        super(DavFsDataItem, self).__init__(path, store)

    def get_content(self, max_length=None):
        obj = self.store.dav_fs.open(self.tarfile_path, 'rb')
        with closing(tarfile.open(fileobj=obj)) as data_archive:
            f = data_archive.extractfile(self.path)
            if max_length:
                content = f.read(max_length)
            else:
                content = f.read()
            f.close()
            return content

    # mandatory repeat
    content = property(fget=get_content)

    def _get_info(self):
        obj = self.store.dav_fs.open(self.tarfile_path, 'rb')
        with closing(tarfile.open(fileobj=obj)) as data_archive:
            return data_archive.getmember(self.path)
        return tarfile.TarInfo()


@component
class DavFsDataStore(ArchivingFileSystemDataStore):
    """ArchivingFileSystemDataStore that archives to webdav storage"""

    data_item_class = DavFsDataItem

    def __init__(self, root, dav_url, dav_user=None, dav_pw=None):
        super(DavFsDataStore, self).__init__(root)
        parsed = urlparse(dav_url)
        self.dav_user = dav_user or parsed.username
        self.dav_pw = dav_pw or parsed.password
        self.dav_url = parsed.geturl()
        self.dav_fs = DAVFS(url=self.dav_url, credentials={'username': self.dav_user, 'password': self.dav_pw})

    def __getstate__(self):
        return {'root': self.root, 'dav_url': self.dav_url, 'dav_user': self.dav_user, 'dav_pw': self.dav_pw}

    def find_new_data(self, timestamp):
        """Finds newly created/changed data items"""
        new_files = self._find_new_data_files(timestamp)
        label = timestamp.strftime(TIMESTAMP_FORMAT)
        archive_paths = self._archive(label, new_files)
        return [DavFsDataItem(path, self).generate_key()
                for path in archive_paths]

    def _archive(self, label, files, delete_originals=True):
        """
        Archives files and, by default, deletes the originals.
        """
        fs = self.dav_fs
        if not fs.isdir(self.archive_store):
            fs.makedir(self.archive_store, recursive=True)
        tf_obj = fs.open(os.path.join(self.archive_store, label + ".tar.gz"), mode='wb')
        with tarfile.open(fileobj=tf_obj, mode='w:gz') as tf:
            logging.info("Archiving data to file %s" % tf.name)
            # Add data files
            archive_paths = []
            for file_path in files:
                archive_path = os.path.join(label, file_path)
                tf.add(os.path.join(self.root, file_path), archive_path)
                archive_paths.append(archive_path)
            tf.close()
        tf_obj.close()

        # Delete original files.
        if delete_originals:
            for file_path in files:
                os.remove(os.path.join(self.root, file_path))
        self._last_label = label # useful for testing
        return archive_paths
