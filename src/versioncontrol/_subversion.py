import pysvn
import os

from base import Repository, WorkingCopy

def may_have_working_copy():
    print "Testing for existence of ", os.path.join(os.getcwd(), ".svn")
    return os.path.exists(os.path.join(os.getcwd(), ".svn"))

def get_working_copy():
    return SubversionWorkingCopy()

def get_repository(url):
    return SubversionRepository(url)


class SubversionWorkingCopy(WorkingCopy):
    
    def __init__(self):
        client = pysvn.Client()
        url = client.info(".").url
        self.repository = SubversionRepository(url)
        self.repository.working_copy = self

    def current_version(self):
        return self.repository._client.info('.').revision.number

    def use_version(self, version):
        self.repository._client.update(
            '.',
            revision=pysvn.Revision(pysvn.opt_revision_kind.number, version))

    def use_latest_version(self):
        self.repository._client.update('.')

    def status(self):
        changes = self.repository._client.status('.')
        status_dict = {}
        status_dict['modified'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.modified]
        status_dict['added'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.added]
        status_dict['removed'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.deleted]
        status_dict['deleted'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.missing]
        status_dict['unknown'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.unversioned]
        status_dict['clean'] = [f.path for f in changes if f.text_status == pysvn.wc_status_kind.normal]
        return status_dict

    def has_changed(self):
        status = self.status()
        changed = False
        for st in 'modified', 'removed', 'deleted':
            if status[st]:
                changed = True
                break
        return changed
        

class SubversionRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._client = pysvn.Client()
        # need to add a check that there is a valid Subversion repository at the URL,
        # short of doing a checkout. e.g. svn info URL
        self.working_copy = None
    
    def checkout(self, path='.'):
        try:
            self._client.checkout(self.url, ".")
        except pysvn._pysvn.ClientError: # assume this is an 'object of the same name already exists' error
            repos_contents = self._client.ls(self.url)
            os.mkdir(".smt_backup")
            for entry in repos_contents:
                filename = entry["name"][len(self.url)+1:]
                if os.path.exists(filename):
                    os.rename(filename,os.path.join(".smt_backup", filename))
            self._client.checkout(self.url, ".")
        self.working_copy = SubversionWorkingCopy()

    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
        