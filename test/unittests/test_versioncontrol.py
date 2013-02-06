"""
Unit tests for the sumatra.versioncontrol package
"""

from __future__ import with_statement
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
import pickle
import tempfile
import shutil

from sumatra.versioncontrol._mercurial import MercurialRepository, MercurialWorkingCopy, may_have_working_copy
try:
    from sumatra.versioncontrol._subversion import SubversionRepository, SubversionWorkingCopy
    have_pysvn = True
except ImportError:
    have_pysvn = False
try:
    from sumatra.versioncontrol._git import GitRepository, GitWorkingCopy
    have_git = True
except ImportError:
    have_git = False
try:
    from sumatra.versioncontrol._bazaar import BazaarRepository, BazaarWorkingCopy
    have_bzr = True
except ImportError:
    have_bzr = False
from sumatra.versioncontrol import get_repository, get_working_copy, VersionControlError

skip_ci = False
if "JENKINS_SKIP_TESTS" in os.environ:
    skip_ci = os.environ["JENKINS_SKIP_TESTS"] == "1"


class BaseTestWorkingCopy(object):
    
    def change_file(self):
        with open("%s/romans.param" % self.tmpdir) as f:
            content = f.read()
        with open("%s/romans.param" % self.tmpdir, "w") as f:
            f.write(content)
            f.write("omega = 42\n")

    def read_parameters(self, filename):
        P = {}
        with open(filename) as f:
            for line in f:
                name, value = line.split("=")
                P[name.strip()] = eval(value)
        return P
        
    def test__has_changed(self):
        self.assertEqual(self.wc.has_changed(), False)
        self.change_file()
        self.assertEqual(self.wc.has_changed(), True)
        
    def test__diff(self):
        self.assertEqual(self.wc.diff(), "")
        self.change_file()
        assert "+omega = 42" in self.wc.diff()
    
    def test__current_version(self):
        self.assertEqual(self.wc.current_version(), self.latest_version)
    
    def test__use_version(self):
        P = self.read_parameters("%s/default.param" % self.tmpdir)
        self.assertEqual(self.read_parameters("%s/default.param" % self.tmpdir)['seed'],
                         65785)
        self.wc.use_version(self.previous_version)
        self.assertEqual(self.read_parameters("%s/default.param" % self.tmpdir)['seed'],
                         65784)
        
    def test__use_latest_version(self):
        self.wc.use_version(self.previous_version)
        self.assertEqual(self.wc.current_version(), self.previous_version)
        self.wc.use_latest_version()
        self.assertEqual(self.wc.current_version(), self.latest_version)

    def test__contains(self):
        self.assert_(self.wc.contains("romans.param"))


class TestMercurialWorkingCopy(unittest.TestCase, BaseTestWorkingCopy):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/mercurial")
        os.symlink("%s/hg" % self.repository_path, "%s/.hg" % self.repository_path)
        self.repos = MercurialRepository("file://%s" % self.repository_path)
        self.tmpdir = tempfile.mkdtemp()
        self.repos.checkout(self.tmpdir)
        self.wc = MercurialWorkingCopy(self.tmpdir)
        self.latest_version = "7ba7d226aefe"
        self.previous_version = "2f63951b5f32"
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.repository_path)
        shutil.rmtree(self.tmpdir)

    def test__status(self):
        self.assertEqual(self.wc.status(),
                         {'modified': set([]), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['EGG-INFO/PKG-INFO', 'default.param',
                                        'main.py', 'romans.param',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})
        self.change_file()
        self.assertEqual(self.wc.status(),
                         {'modified': set(['romans.param']), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['EGG-INFO/PKG-INFO', 'default.param',
                                        'main.py',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})


#@unittest.skipUnless(have_git, "Could not import git") # 
class TestGitWorkingCopy(unittest.TestCase, BaseTestWorkingCopy):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/git")
        os.symlink("%s/git" % self.repository_path, "%s/.git" % self.repository_path)
        self.repos = GitRepository(self.repository_path)
        self.tmpdir = tempfile.mkdtemp()
        self.repos.checkout(self.tmpdir)
        self.wc = GitWorkingCopy(self.tmpdir)
        self.latest_version = "38598c93c7036a1c44bbb6075517243edfa88860"
        self.previous_version = "3491ce1d9a66abc9d49d5844ee05167c6a854ad9"
        
    def tearDown(self):
        os.unlink("%s/.git" % self.repository_path)
        shutil.rmtree(self.tmpdir)
TestGitWorkingCopy = unittest.skipUnless(have_git, "Could not import git")(TestGitWorkingCopy) # not using as class decorator for the sake of Python 2.5


#@unittest.skipUnless(have_pysvn, "Could not import pysvn")
class TestSubversionWorkingCopy(unittest.TestCase, BaseTestWorkingCopy):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/subversion")
        self.repos = SubversionRepository("file://%s" % self.repository_path)
        self.tmpdir = tempfile.mkdtemp()
        self.repos.checkout(self.tmpdir)
        self.wc = SubversionWorkingCopy(self.tmpdir)
        self.latest_version = "3"
        self.previous_version = "1"
        
    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    #def test__status(self):
    #    self.assertEqual(self.wc.status()['modified'], [])
    #    self.change_file()
    #    self.assertEqual(os.path.basename(self.wc.status()['modified'][0]), 'romans.param')
        
    def test__status(self):
        self.assertEqual(self.wc.status(),
                         {'modified': set([]), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['EGG-INFO', 'subpackage',
                                        'EGG-INFO/PKG-INFO', 'default.param',
                                        'main.py', 'romans.param',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})
        self.change_file()
        self.assertEqual(self.wc.status(),
                         {'modified': set(['romans.param']), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['EGG-INFO', 'subpackage',
                                        'EGG-INFO/PKG-INFO', 'default.param',
                                        'main.py',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})

TestSubversionWorkingCopy = unittest.skipUnless(have_pysvn, "Could not import pysvn")(TestSubversionWorkingCopy)


#@unittest.skipUnless(have_bzr, "Could not import bzrlib")
class TestBazaarWorkingCopy(unittest.TestCase, BaseTestWorkingCopy):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/bazaar")
        os.symlink("%s/bzr" % self.repository_path, "%s/.bzr" % self.repository_path)
        self.repos = BazaarRepository(self.repository_path)
        self.tmpdir = tempfile.mkdtemp()
        self.repos.checkout(self.tmpdir)
        self.wc = BazaarWorkingCopy(self.tmpdir)
        self.latest_version = "4"
        self.previous_version = "1"
        
    def tearDown(self):
        os.unlink("%s/.bzr" % self.repository_path)
        shutil.rmtree(self.tmpdir)
        
    def test__status(self):
        self.assertEqual(self.wc.status(),
                         {'modified': set([]), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['subpackage',
                                        'default.param',
                                        'main.py', 'romans.param',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})
        self.change_file()
        self.assertEqual(self.wc.status(),
                         {'modified': set(['romans.param']), 'removed': set([]),
                          'missing': set([]), 'unknown': set([]),
                          'added': set([]),
                          'clean': set(['subpackage',
                                        'default.param',
                                        'main.py',
                                        'subpackage/__init__.py',
                                        'subpackage/somemodule.py'])})

TestBazaarWorkingCopy = unittest.skipUnless(have_bzr, "Could not import bzrlib")(TestBazaarWorkingCopy)


class BaseTestRepository(object):
    
    def test__pickling(self):
        r = self._create_repository()
        dump = pickle.dumps(r)
        r2 = pickle.loads(dump)
        self.assertEqual(r.url, r2.url)
    
    def test__init(self):
        r = self._create_repository()
        self.assertEqual(r.url, self.repository_path)

    def test__checkout_of_remote_repos(self):
        tmpdir = tempfile.mkdtemp()
        r = self._create_repository()
        r.checkout(path=tmpdir)
        repos_files = os.listdir(tmpdir)
        repos_files.remove(self.special_dir)
        project_files = os.listdir("../example_projects/python")
        if "main.pyc" in project_files:
            project_files.remove("main.pyc")
        self.assertEqual(set(repos_files), set(project_files))
        shutil.rmtree(tmpdir)

    def test__str(self):
        r = self._create_repository()
        str(r)

    def test__eq(self):
        r1 = self._create_repository()
        r2 = self._create_repository()
        self.assertEqual(r1, r2)


class TestMercurialRepository(unittest.TestCase, BaseTestRepository):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/mercurial")
        os.symlink("%s/hg" % self.repository_path, "%s/.hg" % self.repository_path)
        self.special_dir = ".hg"
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.repository_path)
    
    def _create_repository(self):
        return MercurialRepository("file://%s" % self.repository_path)
        
    def test__init(self):
        r = self._create_repository()
        self.assertEqual(r._repository.url(), "file:%s" % self.repository_path)

    def test__exists__with_nonexistent_repos__should_return_False(self):
        repos = MercurialRepository("file:///tmp/")
        self.assertFalse(repos.exists)
    
    def test__can_create_project_in_subdir(self):
        #Test if a Sumatra project can be created in one of the subdirectories of a repository
        tmpdir = tempfile.mkdtemp()
        r = self._create_repository()
        r.checkout(path=tmpdir)
        # get a working copy from the subdirectory
        wc = get_working_copy(os.path.join(tmpdir, 'subpackage')).repository.url
        # is the working copy path same as the repo path?
        self.assertEqual(wc, tmpdir)
        shutil.rmtree(tmpdir)
        

#@unittest.skipUnless(have_git, "Could not import git")
class TestGitRepository(unittest.TestCase, BaseTestRepository):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/git")
        try:
            os.symlink("%s/git" % self.repository_path, "%s/.git" % self.repository_path)
        except OSError:
            pass
        self.special_dir = ".git"
        
    def tearDown(self):
        os.unlink("%s/.git" % self.repository_path)
    
    def _create_repository(self):
        return GitRepository(self.repository_path)

    def test__exists__with_nonexistent_repos__should_return_False(self):
        repos = GitRepository("/tmp/")
        self.assertFalse(repos.exists)

    def test__can_create_project_in_subdir(self):
        #Test if a Sumatra project can be created in one of the subdirectories of a repository
        tmpdir = tempfile.mkdtemp()
        r = self._create_repository()
        r.checkout(path=tmpdir)
        # get a working copy from the subdirectory
        wc = get_working_copy(os.path.join(tmpdir, 'subpackage')).repository.url
        # is the working copy path same as the repo path?
        self.assertEqual(wc, tmpdir)
        shutil.rmtree(tmpdir)
TestGitRepository = unittest.skipUnless(have_git, "Could not import git")(TestGitRepository)


#@unittest.skipUnless(have_pysvn, "Could not import pysvn")
class TestSubversionRepository(unittest.TestCase, BaseTestRepository):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/subversion")
        self.special_dir = ".svn"
        
    def _create_repository(self):
        return SubversionRepository("file://%s" % self.repository_path)
    
    def test__init(self):
        r = self._create_repository()
        assert hasattr(r._client, "checkout")
        
    def test__init__with_nonexistent_repos__should_raise_Exception(self):
        self.assertRaises(Exception, SubversionRepository, "file:///tmp/chnseriguchs")
   
    @unittest.skipIf(skip_ci, "Skipping test on CI server")
    def test__checkout__with_nonexistent_repos__should_raise_Exception(self):
        r = self._create_repository()
        self.assertRaises(Exception, r.checkout, path="file:///tmp/")
        shutil.rmtree("file:") # this is not quite what's supposed to happen
TestSubversionRepository = unittest.skipUnless(have_pysvn, "Could not import pysvn")(TestSubversionRepository)


#@unittest.skipUnless(have_bzr, "Could not import bzrlib")
class TestBazaarRepository(unittest.TestCase, BaseTestRepository):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/bazaar")
        try:
            os.symlink("%s/bzr" % self.repository_path, "%s/.bzr" % self.repository_path)
        except OSError:
            pass
        self.special_dir = ".bzr"
        
    def tearDown(self):
        os.unlink("%s/.bzr" % self.repository_path)
    
    def _create_repository(self):
        return BazaarRepository(self.repository_path)

    def test__exists__with_nonexistent_repos__should_return_False(self):
        repos = BazaarRepository("/tmp/")
        self.assertFalse(repos.exists)

    def test__checkout_of_remote_repos(self):
        tmpdir = tempfile.mkdtemp()
        r = self._create_repository()
        r.checkout(path=tmpdir)
        repos_files = os.listdir(tmpdir)
        repos_files.remove(self.special_dir)
        project_files = os.listdir("../example_projects/python")
        project_files.remove('EGG-INFO')
        if "main.pyc" in project_files:
            project_files.remove("main.pyc")
        self.assertEqual(set(repos_files), set(project_files))
        shutil.rmtree(tmpdir)
TestBazaarRepository = unittest.skipUnless(have_bzr, "Could not import bzrlib")(TestBazaarRepository)


class TestMercurialModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/mercurial")
        try:
            os.symlink("%s/hg" % self.repository_path, "%s/.hg" % self.repository_path)
        except OSError:
            pass
        self.repos = MercurialRepository("file://%s" % self.repository_path)
        self.tmpdir = tempfile.mkdtemp()
        self.repos.checkout(self.tmpdir)
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.repository_path)
        shutil.rmtree(self.tmpdir)
    
    def test__may_have_working_copy(self):
        have_wc = may_have_working_copy(self.tmpdir)
        assert have_wc == True
        
    def test__may_have_working_copy_with_submodule(self):
        path = os.path.join(self.tmpdir, "subpackage")
        have_wc = may_have_working_copy()
        assert have_wc == True


#@unittest.skipUnless(have_pysvn, "Could not import pysvn")
class TestSubversionModuleFunctions(unittest.TestCase):
    pass


class TestPackageFunctions(unittest.TestCase):
    
    def setUp(self):
        self.hg_repos_path = os.path.abspath("../example_repositories/mercurial")
        try:
            os.symlink("%s/hg" % self.hg_repos_path, "%s/.hg" % self.hg_repos_path)
        except OSError:
            pass
        self.basepath = os.path.abspath("%s/../example_repositories/" % os.getcwd())
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.hg_repos_path)
    
    def test__get_repository__from_url(self):
        if have_pysvn:
            repos = get_repository("file://%s/subversion" % self.basepath)
            assert isinstance(repos, SubversionRepository)
        repos = get_repository("file://%s/mercurial" % self.basepath)
        assert isinstance(repos, MercurialRepository), type(repos)
        
    def test__get_repository__from_invalid_url_should_raise_Exception(self):
        self.assertRaises(VersionControlError, get_repository, "file:///tmp/iugnoirutgvnir")

    @unittest.skipUnless(have_pysvn, "Could not import pysvn")
    def test__get_repository_from_working_copy(self):
        repos = SubversionRepository("file://%s/subversion" % self.basepath)
        tmpdir = tempfile.mkdtemp()
        repos.checkout(tmpdir)
        orig_dir = os.getcwd()
        os.chdir(tmpdir)
        repos1 = get_repository(None)
        os.chdir(orig_dir)
        self.assertEqual(repos, repos1)
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
