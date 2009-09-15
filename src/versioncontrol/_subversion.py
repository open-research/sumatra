import pysvn
import os

from base import Repository, WorkingCopy

def may_have_working_copy():
    return os.path.exists(os.path.join(os.getcwd(), ".svn"))

def get_working_copy():
    return SubversionWorkingCopy()

def get_repository(url):
    return SubversionRepository(url)


class SubversionWorkingCopy(WorkingCopy):
    
    def __init__(self):
        self._client = pysvn.Client()
        url = self._client.info(".").url
        self.repository = SubversionRepository(url)
        self.repository.working_copy = self


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
            