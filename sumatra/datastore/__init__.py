"""
The datastore module provides an abstraction layer around data storage,
allowing different methods of storing simulation/analysis results (local
filesystem, remote filesystem, database, etc.) to provide a common interface.

Currently, only local filesystem storage is supported.

Classes
-------

FileSystemDataStore - provides methods for accessing files stored on a local file
                      system, under a given root directory.
ArchivingFileSystemDataStore - provides methods for accessing files written to
                      a local file system then archived as .tar.gz.
MirroredFileSystemDataStore - provides methods for accessing files written to
                      a local file system then mirrored to a web server

Functions
---------

get_data_store() - return a DataStore object based on a class name and
                   constructor arguments.


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from .base import DataStore, DataKey, IGNORE_DIGEST
from .filesystem import FileSystemDataStore
from .archivingfs import ArchivingFileSystemDataStore
from .mirroredfs import MirroredFileSystemDataStore
from ..core import registry


def get_data_store(type, parameters):
    cls = registry.components[DataStore][type]
    return cls(**parameters)
