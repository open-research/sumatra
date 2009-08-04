from mercurial import hg, ui
import os

from base import Repository, WorkingCopy


def may_have_working_copy():
    return os.path.exists(os.path.join(os.getcwd(), ".hg"))

def get_working_copy():
    return MercurialWorkingCopy()

def get_repository(url):
    return MercurialRepository(url)


class MercurialWorkingCopy(WorkingCopy):

    def __init__(self):
        self.repository = MercurialRepository(os.getcwd()) ###### stub
        self.repository.working_copy = self


class MercurialRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._ui = ui.ui()  # get a ui object
        self._repository = hg.repository(self._ui, url)
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        if self.url == path:
            # update
            hg.update(self._repository, None)
        else:
            # can't clone into an existing directory, so we create
            # an empty repository and then do a pull and update
            local_repos = hg.repository(self._ui, path, create=True)
            local_repos.pull(self._repository)
            hg.update(local_repos, None)
            
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']