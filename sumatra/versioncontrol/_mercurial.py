"""
Defines the Sumatra version control interface for Mercurial.

Classes
-------

MercurialWorkingCopy
MercurialRepository


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import hgapi
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
from base import VersionControlError, UncommittedModificationsError
from base import Repository, WorkingCopy
from ..core import registry


def vectorized(generator_func):
    def wrapper(*args, **kwargs):
        return list(generator_func(*args, **kwargs))
    return functools.update_wrapper(wrapper, generator_func)


class MercurialWorkingCopy(WorkingCopy):
    name = "mercurial"

    def __init__(self, path=None):
        WorkingCopy.__init__(self, path)
        self.path = findrepo(self.path)
        self.repository = MercurialRepository(self.path)

    @property
    def exists(self):
        return bool(self.path and findrepo(self.path))

    def current_version(self):
        if hasattr(self.repository._repository, 'workingctx'):  # handle different versions of Mercurial
            ctx = self.repository._repository.workingctx().parents()[0]
        else:
            ctx = self.repository._repository.parents()[0]
        return binascii.hexlify(ctx.node()[:6])

    def use_version(self, version):
        if self.has_changed():
            raise UncommittedModificationsError(self.status())
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
        status = self.status()  # for some reason, calling "status()" sometimes changes the status. Need to investigate further, but calling it twice seems to work, as a temporary hack.
        changed = False
        for st in 'modified', 'removed', 'missing':
            if status[st]:
                print "!!!!!", st, status[st]
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
                return ctx.filectx(ctx.files()[0]).data()  # presume that we have only one file [0]
            i += 1

    def get_username(self):
        return self.repository._repository.ui.username()


class MercurialRepository(Repository):
    name = "mercurial"
    use_version_cmd = "hg update -r"
    apply_patch_cmd = "hg import --no-commit"

    def __init__(self, url, upstream=None):
        Repository.__init__(self, url, upstream)
        self._repository = hgapi.Repo(url)
        self.upstream = self.upstream or self._get_upstream()

    @property
    def exists(self):
        try:
            self._repository.hg_status()
        except hgapi.HgException:
            return False
        else:
            return True

    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        if self.url == path:
            # update
            self._repository.update(reference="") # hgapi expects reference
        else:
            self._repository.hg_clone(url=self.url, path=path)

    def get_working_copy(self, path=None):
        return MercurialWorkingCopy(path)

    def _get_upstream(self):
        if self.exists:
            return self._repository.hg_paths()['default']


registry.register(MercurialRepository)
registry.register(MercurialWorkingCopy)
