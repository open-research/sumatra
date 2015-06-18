"""
Defines the Sumatra version control interface for Git.

Classes
-------

GitWorkingCopy
GitRepository


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

import logging
import git
import os
import shutil
from distutils.version import LooseVersion
from configparser import NoSectionError, NoOptionError
try:
    from git.errors import InvalidGitRepositoryError, NoSuchPathError
except:
    from git.exc import InvalidGitRepositoryError, NoSuchPathError
from .base import Repository, WorkingCopy, VersionControlError
from ..core import component


logger = logging.getLogger("Sumatra")


def check_version():
    if not hasattr(git, "Repo"):
        raise VersionControlError(
            "GitPython not installed. There is a 'git' package, but it is not "
            "GitPython (https://pypi.python.org/pypi/GitPython/)")
    minimum_version = '0.3.5'
    if LooseVersion(git.__version__) < LooseVersion(minimum_version):
        raise VersionControlError(
            "Your Git Python binding is too old. You require at least "
            "version {}. You can install the latest version e.g. via "
            "'pip install -U gitpython'".format(minimum_version))


def findrepo(path):
    check_version()
    try:
        repo = git.Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return
    else:
        return os.path.dirname(repo.git_dir)


@component
class GitWorkingCopy(WorkingCopy):
    """
    An object which allows various operations on a Git working copy.
    """
    name = "git"

    def __init__(self, path=None):
        check_version()
        WorkingCopy.__init__(self, path)
        self.path = findrepo(self.path)
        self.repository = GitRepository(self.path)

    @property
    def exists(self):
        return bool(self.path and findrepo(self.path))

    def current_version(self):
        head = self.repository._repository.head
        try:
            return head.commit.hexsha
        except AttributeError:
            return head.commit.sha

    def use_version(self, version):
        logger.debug("Using git version: %s" % version)
        if version is not 'master':
            assert not self.has_changed()
        g = git.Git(self.path)
        g.checkout(version)

    def use_latest_version(self):
        self.use_version('master')  # note that we are assuming all code is in the 'master' branch

    def status(self):
        raise NotImplementedError()

    def has_changed(self):
        return self.repository._repository.is_dirty()

    def diff(self):
        """Difference between working copy and repository."""
        g = git.Git(self.path)
        return g.diff('HEAD', color='never')

    def content(self, digest, main_file=None):
        """Get the file content from repository."""
        repo = git.Repo(self.path)
        for item in repo.iter_commits('master'):
            if item.hexsha == digest:
                curtree = item.tree
                if main_file is None:
                    file_content = curtree.blobs[0].data_stream.read() # Get the latest added file content.
                elif '/' in main_file:
                    path_to_mainfile = main_file.split('/')
                    pardir_list, main_file = path_to_mainfile[:-1], path_to_mainfile[-1]
                    for dirname in pardir_list:
                        for subtree in curtree.trees:
                            if subtree.name == dirname:
                                curtree = subtree
                                break
                        else:
                            return 'File content not found'
                for blob in curtree.blobs:
                    if blob.name == main_file:
                        file_content = blob.data_stream.read()
                        return file_content

    def contains(self, path):
        """Does the repository contain the file with the given path?"""
        return path in self.repository._repository.git.ls_files().split()

    def get_username(self):
        config = self.repository._repository.config_reader()
        try:
            username, email = (config.get('user', 'name'), config.get('user', 'email'))
        except (NoSectionError, NoOptionError):
            return ""
        return "%s <%s>" % (username, email)


def move_contents(src, dst):
    for file in os.listdir(src):
        src_path = os.path.join(src, file)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, os.path.join(dst, file))
        else:
            shutil.copy2(src_path, dst)
    shutil.rmtree(src)


@component
class GitRepository(Repository):
    name = "git"
    use_version_cmd = "git checkout"
    apply_patch_cmd = "git apply"

    def __init__(self, url, upstream=None):
        check_version()
        Repository.__init__(self, url, upstream)
        self.__repository = None
        self.upstream = self.upstream or self._get_upstream()

    @property
    def exists(self):
        try:
            self._repository
        except VersionControlError:
            pass
        return bool(self.__repository)

    @property
    def _repository(self):
        if self.__repository is None:
            try:
                self.__repository = git.Repo(self.url)
            except (InvalidGitRepositoryError, NoSuchPathError) as err:
                raise VersionControlError("Cannot access Git repository at %s: %s" % (self.url, err))
        return self.__repository

    def checkout(self, path="."):
        """Clone a repository."""
        path = os.path.abspath(path)
        g = git.Git(path)
        if self.url == path:
            # already have a repository in the working directory
            pass
        else:
            tmpdir = os.path.join(path, "tmp_git")
            g.clone(self.url, tmpdir)
            move_contents(tmpdir, path)
        self.__repository = git.Repo(path)

    def get_working_copy(self, path=None):
        return GitWorkingCopy(path)

    def _get_upstream(self):
        if self.exists:
            config = self._repository.config_reader()
            if config.has_option('remote "origin"', 'url'):
                return config.get('remote "origin"', 'url')
