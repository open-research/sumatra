"""
Defines the Sumatra version control interface for Git.

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

from base import Repository, WorkingCopy, VersionControlError

def check_version():
    if git.__version__.split(".")[1] < 2:
        raise VersionControlError("Your Git Python binding is too old. You require at least version 0.2.0-beta1.")

def may_have_working_copy(path=None):
    """Test whether there is a Git working copy at the given path."""
    check_version()
    path = path or os.getcwd()
    if git.repo.is_git_dir(os.path.join(path, ".git")):
        return os.path.exists(os.path.join(path, ".git"))
    else:
        return False

def get_working_copy(path=None):
    """Return a GitWorkingCopy instance for the given path, or the current
    directory if the path is not given."""
    return GitWorkingCopy(path)

def get_repository(url):
    """Return a GitRepository instance for the given url."""
    return GitRepository(url)


class GitWorkingCopy(WorkingCopy):
    """
    An object which allows various operations on a Git working copy.
    """

    def __init__(self, path=None, repository=None):
        check_version()
        WorkingCopy.__init__(self)
        self.path = path or os.getcwd()
        self.repository = repository or GitRepository(self.path)
        self.repository.working_copy = self

    def current_version(self):
        head = self.repository._repository.head
        return head.commit.sha
    
    def use_version(self, version):
        assert not self.has_changed()
        g = git.Git(self.path)
        g.checkout(version)

    def use_latest_version(self):
        self.use_version('master') # note that we are assuming all code is in the 'master' branch
        
    def status(self):
        raise NotImplementedError()   

    def has_changed(self):
        return self.repository._repository.is_dirty()
    
    def diff(self):
        """Difference between working copy and repository."""
        g = git.Git(self.path)
        return g.diff('HEAD')
        

class GitRepository(Repository):
    
    def __init__(self, url):
        check_version()
        Repository.__init__(self, url)
        self.working_copy = None
        self.checkout(url)
            
    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        g = git.Git(path)       
        if self.url == path:
            # already have a repository in the working directory
            pass
        else:
            g.clone(self.url, path)           
        self._repository = git.Repo(path)
        self.working_copy = GitWorkingCopy(path, repository=self)
    
    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'wc': self.working_copy}
    
    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.working_copy = state['wc']
