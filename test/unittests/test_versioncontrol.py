"""
Unit tests for the sumatra.versioncontrol package
"""

from __future__ import with_statement
import unittest
import os
import pickle
import tempfile
import shutil
from sumatra.versioncontrol._mercurial import MercurialRepository, MercurialWorkingCopy, may_have_working_copy
from sumatra.versioncontrol._subversion import SubversionRepository, SubversionWorkingCopy
from sumatra.versioncontrol import get_repository

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
    
    def test__init(self):
        self.assertEqual(self.wc.repository.working_copy, self.wc)
        
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
        self.assertEqual(self.wc.status(), {'modified': [], 'removed': [],
                                            'deleted': [], 'unknown': []})
        self.change_file()
        self.assertEqual(self.wc.status(), {'modified': ['romans.param'], 'removed': [],
                                            'deleted': [], 'unknown': []})


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

    def test__status(self):
        self.assertEqual(self.wc.status()['modified'], [])
        self.change_file()
        self.assertEqual(os.path.basename(self.wc.status()['modified'][0]), 'romans.param')
        

class TestMercurialRepository(unittest.TestCase):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/mercurial")
        os.symlink("%s/hg" % self.repository_path, "%s/.hg" % self.repository_path)
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.repository_path)
        
    def test__init(self):
        r = MercurialRepository("file://%s" % self.repository_path)
        self.assertEqual(r._repository.url(), "file:%s" % self.repository_path)

    def test__init__with_nonexistent_repos__should_raise_Exception(self):
        self.assertRaises(Exception, MercurialRepository, "file:///tmp/")

    def test__pickling(self):
        r = MercurialRepository("file://%s" % self.repository_path)
        dump = pickle.dumps(r)
        r2 = pickle.loads(dump)
        self.assertEqual(r.url, r2.url)
        self.assertEqual(r.working_copy, r2.working_copy)
        
    def test__checkout_of_remote_repos(self):
        tmpdir = tempfile.mkdtemp()
        r = MercurialRepository("file://%s" % self.repository_path)
        r.checkout(path=tmpdir)
        repos_files = os.listdir(tmpdir)
        repos_files.remove(".hg")
        project_files = os.listdir("../example_projects/python")
        if "main.pyc" in project_files:
            project_files.remove("main.pyc")
        self.assertEqual(repos_files, project_files)
        shutil.rmtree(tmpdir)

    def test__str(self):
        r = MercurialRepository("file://%s" % self.repository_path)
        str(r)
        
    def test__eq(self):
        r1 = MercurialRepository("file://%s" % self.repository_path)
        r2 = MercurialRepository("file://%s" % self.repository_path)
        self.assertEqual(r1, r2)
        

class TestSubversionRepository(unittest.TestCase):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/subversion")
    
    def test__init(self):
        r = SubversionRepository("file://%s" % self.repository_path)
        assert hasattr(r._client, "checkout")
        
    def test__init__with_nonexistent_repos__should_raise_Exception(self):
        self.assertRaises(Exception, SubversionRepository, "file:///tmp/")

    def test__pickling(self):
        r = SubversionRepository("file://%s" % self.repository_path)
        dump = pickle.dumps(r)
        r2 = pickle.loads(dump)
        self.assertEqual(r.url, r2.url)
        self.assertEqual(r.working_copy, r2.working_copy)
        
    def test__checkout_of_remote_repos(self):
        tmpdir = tempfile.mkdtemp()
        r = SubversionRepository("file://%s" % self.repository_path)
        r.checkout(path=tmpdir)
        repos_files = os.listdir(tmpdir)
        repos_files.remove(".svn")
        project_files = os.listdir("../example_projects/python")
        if "main.pyc" in project_files:
            project_files.remove("main.pyc")
        self.assertEqual(repos_files, project_files)
        shutil.rmtree(tmpdir)
        
    def test__checkout__with_nonexistent_repos__should_raise_Exception(self):
        r = SubversionRepository("file://%s" % self.repository_path)
        self.assertRaises(Exception, r.checkout, path="file:///tmp/")
        shutil.rmtree("file:") # this is not quite what's supposed to happen

class TestMercurialModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.repository_path = os.path.abspath("../example_repositories/mercurial")
        os.symlink("%s/hg" % self.repository_path, "%s/.hg" % self.repository_path)
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


class TestSubversionModuleFunctions(unittest.TestCase):
    pass

class TestPackageFunctions(unittest.TestCase):
    
    def setUp(self):
        self.hg_repos_path = os.path.abspath("../example_repositories/mercurial")
        os.symlink("%s/hg" % self.hg_repos_path, "%s/.hg" % self.hg_repos_path)
        self.basepath = os.path.abspath("%s/../example_repositories/" % os.getcwd())
        
    def tearDown(self):
        os.unlink("%s/.hg" % self.hg_repos_path)
    
    def test__get_repository__from_url(self):
        repos = get_repository("file://%s/subversion" % self.basepath)
        assert isinstance(repos, SubversionRepository)
        repos = get_repository("file://%s/mercurial" % self.basepath)
        assert isinstance(repos, MercurialRepository), type(repos)
        
    def test__get_repository__from_invalid_url_should_raise_Exception(self):
        self.assertRaises(Exception, get_repository, "file:///tmp/")

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
