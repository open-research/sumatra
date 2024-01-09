"""
Defines the Sumatra version control interface for Mercurial.

Classes
-------

MercurialWorkingCopy
MercurialRepository


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import hgapi
import os
import functools
from .base import UncommittedModificationsError
from .base import Repository, WorkingCopy
from ..core import component


def vectorized(generator_func):
    def wrapper(*args, **kwargs):
        return list(generator_func(*args, **kwargs))
    return functools.update_wrapper(wrapper, generator_func)


def findrepo(p):
    while not os.path.isdir(os.path.join(p, ".hg")):
        oldp, p = p, os.path.dirname(p)
        if p == oldp:
            return None
    return p


@component
class MercurialWorkingCopy(WorkingCopy):
    name = "mercurial"

    def __init__(self, path=None):
        WorkingCopy.__init__(self, path)
        self.path = findrepo(self.path)
        self.repository = MercurialRepository(url=self.path)

    @property
    def exists(self):
        return bool(self.path and findrepo(self.path))

    def current_version(self):
        return self.repository._repository.hg_id()

    def use_version(self, version):
        if self.has_changed():
            raise UncommittedModificationsError(self.status())
        self.repository._repository.hg_update(reference=version, clean=True)

    def use_latest_version(self):
        # any changes to the working copy are retained/merged in
        self.repository._repository.hg_update(reference='tip', clean=True)

    def status(self):
        status = self.repository._repository.hg_status(empty=True, clean=True)
        return {'modified': set(status['M'] if 'M' in status else []),
                'removed': set(status['R'] if 'R' in status else []),
                'missing': set(status['!'] if '!' in status else []),
                'unknown': set(status['?'] if '?' in status else []),
                'clean': set(status['C'] if 'C' in status else []),
                'added': set(status['A'] if 'A' in status else [])}

    def has_changed(self):
        status = self.status()
        status = self.status()  # for some reason, calling "status()" sometimes changes the status. Need to investigate further, but calling it twice seems to work, as a temporary hack.
        changed = False
        for st in 'modified', 'removed', 'missing':
            if status[st]:
                print("!!!!!", st, status[st])
                changed = True
                break
        return changed

    def diff(self):
        """Difference between working copy and repository."""
        diffs = self.repository._repository.hg_diff()
        return "".join([entry['diff'] for entry in diffs])

    #def content(self, hex):
    #    repo = self.repository._repository
    #    i = 1
    #    if hex in repo.parents()[0].hex():
    #        ctx = repo.parents()[0]
    #        return ctx.filectx(ctx.files()[0]).data()
    #    while True:
    #        el = repo.parents(i)[0].hex()
    #        if hex in el:
    #            ctx = repo.parents(i)[0]
    #            return ctx.filectx(ctx.files()[0]).data()  # presume that we have only one file [0]
    #        i += 1

    def get_username(self):
        return self.repository._repository.user if self.repository._repository.user else ""


@component
class MercurialRepository(Repository):
    name = "mercurial"
    use_version_cmd = "hg update -r"
    apply_patch_cmd = "hg import --no-commit"

    def __init__(self, url, upstream=None):
        Repository.__init__(self, url, upstream)
        if url is not None and url.startswith('file://'):
            url = url[7:]
        self._repository = hgapi.Repo(url)
        self.upstream = self.upstream or self._get_upstream()

    @property
    def exists(self):
        if self.url is None:
            return False
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
            pass
        else:
            self._repository.hg_clone(url=self.url, path=path)

    def get_working_copy(self, path=None):
        return MercurialWorkingCopy(path)

    def _get_upstream(self):
        if self.exists:
            return self._repository.hg_paths()['default']
