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
    else:
        return False

def get_working_copy(path=None):
    return GitWorkingCopy(path)

def get_repository(url):
    return GitRepository(url)


class GitWorkingCopy(WorkingCopy):

    def __init__(self, path=None):
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.repository = GitRepository(self.path)
        self.repository.working_copy = self

    def current_version(self):
        head = self.repository._repository.commits()[0]
        return head.id
    
    def use_version(self, version):
        pass
        # TODO:
        # this command should move the tree to some older
        # revision (if I have understood git terminology correctly)
        # this is perhaps equivalent to the git checkout command?

    def use_latest_version(self):
        pass
        # TODO:
        # use the last version available from the repo
        
    def status(self):
        # We don't need to use this. 
        pass            

    def has_changed(self):
        return self.repository._repository.is_dirty
    
    def diff(self):
        """Difference between working copy and repository."""
        return self.repository._repository.commit_diff('HEAD')
        

class GitRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self.working_copy = None
            
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        g = git.Git()       
        if self.url == path:
            pass
        elif os.path.exists(path):
            # can't clone into an existing directory
            # suggest we create an empty repository in
            # path and then pull/fetch whatever from url into
            # it.
            raise NotImplementedError("TODO")
        else:
            g.clone(self.url, path)           
        self._repository = git.Repo(path)
        self.working_copy = GitWorkingCopy(path)
    
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
