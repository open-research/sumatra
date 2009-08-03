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
        self._ui = ui.ui()  # get a ui object
        self._repository = hg.repository(self._ui, url)
            
    def checkout(self, path="."):
        """Clone a repository."""
        pass