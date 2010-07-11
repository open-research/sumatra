"""
Defines the Sumatra version control interface for Mercurial.

Classes
-------

MercurialWorkingCopy
MercurialRepository

Functions
---------

may_have_working_copy() - determine whether a .hg subdirectory exists at a given
                          path
get_working_copy()      - return a MercurialWorkingCopy object for a given path
get_repository()        - return a MercurialRepository object for a given URL.
"""

from mercurial import hg, ui, patch
try:
    from mercurial.error import RepoError
except ImportError:
    from mercurial.repo import RepoError
try:
    from mercurial.cmdutil import findrepo
except ImportError:
    from mercurial.dispatch import _findrepo as findrepo
import os
import binascii
from base import VersionControlError

from base import Repository, WorkingCopy


def may_have_working_copy(path=None):
    path = path or os.getcwd()
    return bool(findrepo(path))

def get_working_copy(path=None):
    if may_have_working_copy(path):
        return MercurialWorkingCopy(path)
    else:
        raise VersionControlError("No Mercurial working copy found at %s" % path)

def get_repository(url):
    return MercurialRepository(url)


class MercurialWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.repository = MercurialRepository(self.path)
        self.repository.working_copy = self

    def current_version(self):
        if hasattr(self.repository._repository, 'workingctx'): # handle different versions of Mercurial 
            ctx = self.repository._repository.workingctx().parents()[0]
        else:
            ctx = self.repository._repository.parents()[0]
        return binascii.hexlify(ctx.node()[:6])
    
    def use_version(self, version):
        assert not self.has_changed()
        hg.clean(self.repository._repository, version)

    def use_latest_version(self):
        # any changes to the working copy are retained/merged in
        hg.update(self.repository._repository, 'tip')

    def status(self):
        modified, added, removed, deleted, unknown, ignored, clean = self.repository._repository.status() #unknown=True)
        return {'modified': modified, 'removed': removed,
                'deleted': deleted, 'unknown': unknown}

    def has_changed(self):
        status = self.status()
        changed = False
        for st in 'modified', 'removed', 'deleted':
            if status[st]:
                changed = True
                break
        return changed
    
    def diff(self):
        """Difference between working copy and repository."""
        opts = patch.mdiff.diffopts(nodates=True)
        diff = patch.diff(self.repository._repository, opts=opts)
        return "".join(diff)


class MercurialRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._ui = ui.ui()  # get a ui object
        try:
            self._repository = hg.repository(self._ui, url)
        # need to add a check that this actually is a Mercurial repository
        except (RepoError, Exception), err:
            raise VersionControlError("%s" % err)
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        if self.url == path:
            # update
            hg.update(self._repository, None)
        else:
            # can't clone into an existing directory, so we create
            # an empty repository and then do a pull and update
            local_repos = hg.repository(self._ui, path, create=True)
            local_repos.pull(self._repository)
            hg.update(local_repos, None)
        self.working_copy = MercurialWorkingCopy(path)
    
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
