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
import functools
from base import VersionControlError

from base import Repository, WorkingCopy

def vectorized(generator_func):
    def wrapper(*args, **kwargs):
        return list(generator_func(*args, **kwargs))
    return functools.update_wrapper(wrapper, generator_func)

def may_have_working_copy(path=None):
    path = path or os.getcwd()
    return bool(findrepo(path))

def get_working_copy(path=None):
    repo_dir = findrepo(path or os.getcwd())
    if repo_dir:
        return MercurialWorkingCopy(repo_dir)
    else:
        raise VersionControlError("No Mercurial working copy found at %s" % path)


def get_repository(url):
    repos = MercurialRepository(url)
    if repos.exists:
        return repos
    else:
        raise VersionControlError("Cannot access Mercurial repository at %s" % self.url)    


class MercurialWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.repository = MercurialRepository(self.path)

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
        modified, added, removed, missing, unknown, ignored, clean = self.repository._repository.status(ignored=True, clean=True, unknown=True)
        return {'modified': set(modified), 'removed': set(removed),
                'missing': set(missing), 'unknown': set(unknown),
                'clean': set(clean), 'added': set(added)}

    def has_changed(self):
        status = self.status()
        changed = False
        for st in 'modified', 'removed', 'missing':
            if status[st]:
                changed = True
                break
        return changed
    
    def diff(self):
        """Difference between working copy and repository."""
        opts = patch.mdiff.diffopts(nodates=True)
        diff = patch.diff(self.repository._repository, opts=opts)
        return "".join(diff)

    def content(self, hex):
        repo = self.repository._repository
        i = 1
        if hex in repo.parents()[0].hex():
            ctx = repo.parents()[0] 
            return ctx.filectx(ctx.files()[0]).data()
        while True:
            el = repo.parents(i)[0].hex()
            if hex in el:  
                ctx = repo.parents(i)[0]      
                return ctx.filectx(ctx.files()[0]).data() # presume that we have only one file [0]
            i += 1

    def get_username(self):
        return self.repository._repository.ui.username()


class MercurialRepository(Repository):
    
    def __init__(self, url, upstream=None):
        Repository.__init__(self, url, upstream)
        self.__repository = None
        self.upstream = self.upstream or self._get_upstream()

    @property
    def exists(self):
        try:
            self._repository
        except VersionControlError:
            pass
        return bool(self.__repository)

    @property
    def _repository(self):
        if self.__repository is None:
            try:
                self.__repository = hg.repository(ui.ui(), self.url)
                # need to add a check that this actually is a Mercurial repository
            except (RepoError, Exception), err:
                raise VersionControlError("Cannot access Mercurial repository at %s: %s" % (self.url, err))
        return self.__repository    

    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        if self.url == path:
            # update
            hg.update(self._repository, None)
        else:
            try:
                hg.clone(self._repository.ui, {}, self.url, path, update=True)
            except:  # hg.clone fails for older versions of mercurial, e.g. 1.5
                local_repos = hg.repository(self._repository.ui, path, create=True)
                local_repos.pull(self._repository)
                hg.update(local_repos, None)

    def get_working_copy(self, path=None):
        return get_working_copy(path)

    def _get_upstream(self):
        if self.exists:
            return self._repository.ui.config('paths', 'default')
