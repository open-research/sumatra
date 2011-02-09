"""
Defines the Sumatra version control interface for Bazaar.

Classes
-------

BazaarWorkingCopy
BazaarRepository

Functions
---------

may_have_working_copy() - determine whether a .bzr subdirectory exists at a given
                          path
get_working_copy()      - return a BazaarWorkingCopy object for a given path
get_repository()        - return a BazaarRepository object for a given URL.
"""

from bzrlib.branch import Branch
from bzrlib.workingtree import WorkingTree
from bzrlib import diff
    

import os
import StringIO

from base import VersionControlError
from base import Repository, WorkingCopy

def may_have_working_copy(path=None):
    path = path or os.getcwd()
    return os.path.exists(os.path.join(path, ".bzr"))


def get_working_copy(path=None):
    try:
        return BazaarWorkingCopy(path)
    except:
        raise VersionControlError("No Bazaar working copy found at %s" % path)

def get_repository(url):
    return BazaarRepository(url)


class BazaarWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.workingtree = WorkingTree.open(self.path)
        self.repository = BazaarRepository(self.workingtree.branch.user_url)
        self.repository.working_copy = self
        self._current_version = self.repository._repository.revno()

    def _get_revision_tree(self, version):
        if isinstance(version, basestring):
            version = int(version)
        revision_id = self.workingtree.branch.get_rev_id(version)
        return self.workingtree.branch.repository.revision_tree(revision_id)

    def current_version(self):
        return str(self._current_version)
    
    def use_version(self, version):
        self.use_latest_version()
        assert not self.has_changed()
        rev_tree = self._get_revision_tree(version)
        self.workingtree.revert(old_tree=rev_tree)
        self._current_version = version

    def use_latest_version(self):
        self.workingtree.update()
        self.workingtree.revert()
        self._current_version = self.repository._repository.revno()

    def status(self):
        current_tree = self._get_revision_tree(self._current_version)
        delta = self.workingtree.changes_from(current_tree, want_unversioned=True)
        modified = [i[0] for i in delta.modified]
        deleted = [i[0] for i in delta.removed]
        unknown = [i[0] for i in delta.unversioned]
        added = [i[0] for i in delta.added]
        removed = []
        return {'modified': modified, 'removed': removed,
                'deleted': deleted, 'unknown': unknown,
                'added':added}

    def has_changed(self):
        return self.workingtree.has_changes()
    
    def diff(self):
        """Difference between working copy and repository."""
        iostream = StringIO.StringIO()
        diff.show_diff_trees(self.workingtree.basis_tree(), self.workingtree, iostream)
        # textstream
        return iostream.getvalue()

    def __getstate__(self):
        """For pickling"""
        return {'path': self.path}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['path'])
    

class BazaarRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self.url = url
        try:
            self._repository = Branch.open(url)
        except:
            raise VersionControlError("%s" % "Error opening BzrDir")
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        self._repository.create_checkout(path, lightweight=True)
        self.working_copy = BazaarWorkingCopy(path)
    
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
