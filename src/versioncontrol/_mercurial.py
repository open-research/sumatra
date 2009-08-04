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
            # clone
            hg.clone(self._ui,
                     self._repository, # source
                     path) # dest
            
    def __getstate__(self):
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        self.__init__(state['url'])
        self.working_copy = state['wc']