"""
Defines the Sumatra version control interface for Subversion.

Classes
-------

SubversionWorkingCopy
SubversionRepository

Functions
---------

may_have_working_copy() - determine whether a .svn subdirectory exists at a
                          given path
get_working_copy()      - return a SubversionWorkingCopy object for a given path
get_repository()        - return a SubversionRepository object for a given URL.
"""

import pysvn
import os
import tempfile
import shutil

from base import Repository, WorkingCopy, VersionControlError

def may_have_working_copy(path=None):
    path = path or os.getcwd()
    #print "Testing for existence of ", os.path.join(path, ".svn")
    return os.path.exists(os.path.join(path, ".svn"))

def get_working_copy(path=None):
    return SubversionWorkingCopy(path)

def get_repository(url):
    return SubversionRepository(url)


class SubversionWorkingCopy(WorkingCopy):
    
    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = os.path.realpath(path or os.getcwd())
        client = pysvn.Client()
        url = client.info(self.path).url
        self.repository = SubversionRepository(url)

    def current_version(self):
        return str(self.repository._client.info(self.path).revision.number)

    def use_version(self, version):
        self.repository._client.update(
            self.path,
            revision=pysvn.Revision(pysvn.opt_revision_kind.number, int(version)))

    def use_latest_version(self):
        self.repository._client.update(self.path)

    def status(self):
        changes = self.repository._client.status(self.path)
        status_dict = {}
        offset = len(self.path) + 1
        status_dict['modified'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.modified)
        status_dict['added'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.added)
        status_dict['removed'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.deleted)
        status_dict['missing'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.missing)
        status_dict['unknown'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.unversioned)
        status_dict['clean'] = set(f.path[offset:] for f in changes if f.text_status == pysvn.wc_status_kind.normal)
        if '' in status_dict['clean']:
            status_dict['clean'].remove('')
        return status_dict

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
        tmpdir = tempfile.mkdtemp()
        result = self.repository._client.diff(tmpdir, self.path)
        shutil.rmtree(tmpdir)
        return result


class SubversionRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._client = pysvn.Client()
        # check that there is a valid Subversion repository at the URL,
        # without doing a checkout.
        try:
            self._client.ls(url)
        except pysvn._pysvn.ClientError, errmsg:
            raise VersionControlError(errmsg)
    
    def checkout(self, path='.'):
        try:
            self._client.checkout(self.url, path)
        except pysvn._pysvn.ClientError: # assume this is an 'object of the same name already exists' error
            repos_contents = self._client.ls(self.url)
            os.mkdir(".smt_backup")
            for entry in repos_contents:
                filename = entry["name"][len(self.url)+1:]
                if os.path.exists(filename):
                    os.rename(filename,os.path.join(".smt_backup", filename))
            self._client.checkout(self.url, path)

    def get_working_copy(self, path=None):
        return get_working_copy(path)
