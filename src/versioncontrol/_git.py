"""
Defines the Sumatra version control interface for Git.
Based (heavily) on the Mercurial class

Classes
-------

GitWorkingCopy
GitRepository

Functions
---------

may_have_working_copy() - determine whether a .git subdirectory exists at a given
                          path
get_working_copy()      - return a GitWorkingCopy object for a given path
get_repository()        - return a GitRepository object for a given URL.
"""

import git
import os

from base import Repository, WorkingCopy


def may_have_working_copy(path=None):
    path = path or os.getcwd()
    if git.cmd.is_git_dir(os.path.join(path, ".git")):
        return os.path.exists(os.path.join(path, ".git"))

def get_working_copy(path=None):
    return GitWorkingCopy(path)

def get_repository(url):
    return GitRepository(url)


class GitWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        self.path = path or os.getcwd()
        self.repository = GitRepository(self.path)
        self.repository.working_copy = self

    def current_version(self):
        head = self.repository._repository.commits()[0]
        return head.id
    
    def use_version(self, version):
        pass
        # TODO:
        # What exactly should happen here?

    def use_latest_version(self):
        pass
        # TODO:
        # Shall we use the last version available from the repo? 
        
    def status(self):
        # We don't need to use this.
        pass            

    def has_changed(self):
        changed = False
        if self.repository._repository.is_dirty():
            changed = True
        return changed
    
    def diff(self):
        """Difference between working copy and repository."""
        return self.repository._repository.commit_diff('HEAD')
        

class GitRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._repository = git.Repo(url)
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        
        pass
        # TODO: We need to checkout the last commit?
        # Or we need to clone the last commit somewhere (light branch?)
        
#        path = os.path.abspath(path)
#        if self.url == path:
#            # update
#            hg.update(self._repository, None)
#            
#        else:
#            # can't clone into an existing directory, so we create
#            # an empty repository and then do a pull and update
#            local_repos = hg.repository(self._ui, path, create=True)
#            local_repos.pull(self._repository)
#            hg.update(local_repos, None)
#        self.working_copy = MercurialWorkingCopy()
    
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
