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
    repos = BazaarRepository(url)
    if repos.exists:
        return repos
    else:
        raise VersionControlError("Cannot access Bazaar repository at %s" % self.url)   


class BazaarWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.workingtree = WorkingTree.open(self.path)
        self.repository = BazaarRepository(self.workingtree.branch.user_url)
        #self.repository.working_copy = self
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


class BazaarRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self.url = url
        self.__repository = None
    
    @property
    def exists(self):
        if self._repository:
            return True
    
    @property
    def _repository(self):
        if self.__repository is None:
            try:
                self.__repository = Branch.open(self.url)
            except Exception, err:
                raise VersionControlError("Cannot access Bazaar repository at %s: %s" % (self.url, err))    
        return self.__repository
    
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        self._repository.create_checkout(path, lightweight=True)
        #self.working_copy = BazaarWorkingCopy(path)

    def get_working_copy(self, path=None):
        return get_working_copy(path)
