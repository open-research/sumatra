from mercurial import hg, ui
import os
import binascii

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

    def current_version(self):
        changectx = self.repository._repository.changectx("tip") # need to figure out the currently checkout-out version, not necessarily "tip"
        return binascii.hexlify(changectx.node()[:6])
    

class MercurialRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._ui = ui.ui()  # get a ui object
        self._repository = hg.repository(self._ui, url)
        # need to add a check that this actually is a Mercurial repository
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        print path
        print self.url
        if self.url == path:
            # update
            hg.update(self._repository, None)
        else:
            # can't clone into an existing directory, so we create
            # an empty repository and then do a pull and update
            local_repos = hg.repository(self._ui, path, create=True)
            local_repos.pull(self._repository)
            hg.update(local_repos, None)
        self.working_copy = MercurialWorkingCopy()
            
    def use_version(self, version):
        hg.clean(self._repository, version)
            
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']