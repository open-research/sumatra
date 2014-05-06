"""


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import hashlib
import os.path

IGNORE_DIGEST = "0"*40


class DataStore(object):
    """Base class for data storage abstractions."""

    def __getstate__(self):
        """
        Since each subclass has different attributes, we provide this method
        as a standard way of obtaining these attributes, for database storage,
        etc. Returns a dict.
        """
        raise NotImplementedError

    def copy(self):
        return self.__class__(**self.__getstate__())

    def find_new_data(self, timestamp):
        """Finds newly created/changed data items"""
        raise NotImplementedError

    def get_data_item(self, key):
        """
        Return the file that matches the given key.
        """
        raise NotImplementedError

    def get_content(self, key, max_length=None):
        """
        Return the contents of a file identified by a key.

        If `max_length` is given, the return value will be truncated.
        """
        return self.get_data_item(key).get_content(max_length)

    def delete(self, *keys):
        """
        Delete the files corresponding to the given keys.
        """
        raise NotImplementedError

    def generate_keys(self, *paths):
        """
        Given a number of "paths", return a list of keys enabling the data at
        those paths to be retrieved from this store later.
        """
        return [self.data_item_class(path, self).generate_key() for path in paths]

    def contains_path(self, path):
        """Does the store contain a data item with the given path?"""
        raise NotImplementedError


class DataKey(object):
    """
    Identifies a :class:`DataItem`, and may be used to retrieve a
    :class:`DataItem` from a :class:`DataStore`.

    May also be used to store metadata (e.g. file size, mimetype) and be used as
    a proxy for the :class:`DataItem` on a system where the actual data is not
    available.
    """

    def __init__(self, path, digest, **metadata):
        self.path = path
        self.digest = digest
        self.metadata = metadata

    def __repr__(self):
        return "%s(%s)" % (self.path, self.digest)

    def __eq__(self, other):
        return self.path == other.path and (self.digest == other.digest or IGNORE_DIGEST in (self.digest, other.digest))

    def __ne__(self, other):
        return not self.__eq__(other)


class DataItem(object):
    """Base class for data item classes, that may represent files or database records."""

    def __str__(self):
        return self.path

    @property
    def digest(self):
        """docstring"""
        return hashlib.sha1(self.content).hexdigest()

    def __eq__(self, other):
        if self.size != other.size:
            return False
        elif self.content == other.content: # use digest here?
            return True
        else:
            return self.sorted_content == other.sorted_content

    def __ne__(self, other):
        return not self.__eq__(other)

    def generate_key(self):
        """Generate a :class:`DataKey` uniquely identifying this data item."""
        return DataKey(self.path, self.digest, mimetype=self.mimetype,
                       encoding=self.encoding, size=self.size)

    def get_content(self, max_length=None):
        """
        Return the contents of the data item as a string.

        If *max_length* is specified, return that number of bytes, otherwise
        return the entire content.
        """
        raise NotImplementedError

    def sorted_content(self):
        """Return the contents of the data item, sorted by line."""
        raise NotImplementedError

    def save_copy(self, path):
        """
        Save a copy of the data to a local file.

        If path is an existing directory, the data item path will be appended
        to it, otherwise path is treated as a full path including filename,
        either absolute or relative to the working directory.

        Return the full path of the final file.
        """
        if os.path.isdir(path):
            full_path = os.path.join(path, self.path)
        else:
            full_path = path
        dir = os.path.dirname(full_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(full_path, "w") as fp:
            fp.write(self.content)
        return full_path
