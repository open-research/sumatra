"""
Unit tests for the sumatra.dependency_finder module
"""
from __future__ import print_function
from builtins import str
from builtins import object

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import sumatra.dependency_finder as df
import sys
import os
try:
    import numpy
    have_numpy = True
except ImportError:
    have_numpy = False
import tempfile
import shutil
import warnings

skip_ci = False
if "JENKINS_SKIP_TESTS" in os.environ:
    skip_ci = os.environ["JENKINS_SKIP_TESTS"] == "1"


class MockExecutable(object):
    def __init__(self, name):
        self.name = name
        self.path = name
        
class MockRExecutable(MockExecutable):
    def __init__(self, name):
        self.name = 'R'
        rpath = '/usr/bin/Rscript'
        if os.path.exists(rpath):
            self.path = rpath
        else:
            raise unittest.SkipTest("Can't find Rscript")


@unittest.skipIf(skip_ci, "Skipping test on CI server")
class TestRModuleFunctions(unittest.TestCase):
    def setUp(self):
        self.saved_path = sys.path[:]
        self.cwd = os.getcwd()
        self.example_project = os.path.join(tmpdir, "R")
        assert os.path.exists(self.example_project)
        sys.path.append(os.path.abspath(self.example_project))
        os.chdir(self.example_project)

    def tearDown(self):
        sys.path = self.saved_path
        os.chdir(self.cwd)
        
    def test__r_extern_script(self):
        self.assertEqual(os.path.exists(df.r.r_script_to_find_deps), True)

    def test__r_get_r_dependencies(self):
        rex = MockRExecutable('R')
        myscript_deps = 'pkg::\nname : dplyr \npath : /Library/Frameworks/R.framework/Versions/3.1/Resources/library/dplyr \nversion : 0.4.1 \nsource : CRAN \npkg::\nname : MASS \npath : /Library/Frameworks/R.framework/Versions/3.1/Resources/library/MASS \nversion : 7.3-35 \nsource : CRAN \n'
        status, deps = df.r._get_r_dependencies(rex.path, 'myscript.R', depfinder='myscript.R')
        self.assertEqual(deps, myscript_deps)
        self.assertEqual(status, 0)

    def test__r_parse_deps(self):
        rex = MockRExecutable('R')
        status, deps = df.r._get_r_dependencies(rex.path, 'myscript.R', depfinder='myscript.R')
        list_deps = df.r._parse_deps(deps)
        d1, d2 = list_deps
        self.assertEqual(d1.name, 'dplyr')
        self.assertEqual(d1.source, 'CRAN')
        self.assertEqual(d1.version, '0.4.1')
        self.assertEqual(d2.name, 'MASS')
        self.assertEqual(d2.source, 'CRAN')
        self.assertEqual(d2.version, '7.3-35')


class TestPythonModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        self.cwd = os.getcwd()
        self.example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(self.example_project)
        sys.path.append(os.path.abspath(self.example_project))
        os.chdir(self.example_project)
    
    def tearDown(self):
        sys.path = self.saved_path
        os.chdir(self.cwd)
    
    @unittest.skipUnless(have_numpy, "test requires NumPy")
    def test__find_versions_by_attribute(self):
        import main
        self.assertEqual(df.python.find_version_by_attribute(main), "1.2.3a")
        del main.__version__
        self.assertEqual(df.python.find_version_by_attribute(main), "1.2.3b")
        
    def test__find_versions_from_egg(self):
        dep = df.python.Dependency("main", os.path.join(self.example_project, "main.py"))
        self.assertEqual(dep.version, 'unknown')
        df.python.find_versions_from_egg([dep])
        self.assertEqual(dep.version, "1.2.3egg")
    
    @unittest.skipUnless(have_numpy, "test requires NumPy")
    def test__find_imported_packages(self):
        # the example project has numpy as its only import
        example_project_imports = df.python.find_imported_packages(os.path.join(tmpdir, "python", "main.py"), sys.executable)
        assert "numpy" in list(example_project_imports.keys())
    

class TestCoreModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(self.example_project)
        self.somemodule_path = os.path.abspath(os.path.join(self.example_project, "subpackage", "somemodule.py"))

    def test__find_versions(self):
        #better to test this using mocks
        dep = df.python.Dependency("main", os.path.join(self.example_project, "main.py"))
        df.core.find_versions([dep], [df.python.find_versions_from_egg])
        self.assertEqual(dep.version, "1.2.3egg")

    def test__find_file_full_path(self):
        self.assertEqual(df.core.find_file(os.path.join(self.example_project, "subpackage", "somemodule.py"),
                                           None,
                                           None),
                         self.somemodule_path)
    
    def test__find_file_current_directory(self):
        self.assertEqual(df.core.find_file("somemodule.py",
                                           os.path.join(self.example_project, "subpackage"),
                                           []),
                         self.somemodule_path)
    
    def test__find_file_nonexistentfile(self):
        self.assertRaises(IOError,
                          df.core.find_file,
                          "adifferentmodule.py",
                          os.path.join(self.example_project, "subpackage"),
                          [])
    
    def test__find_versions_from_versioncontrol(self):
        pass
        
class TestMainModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_projects = {
            'python': os.path.join(tmpdir, "python"),
            'neuron': os.path.join(tmpdir, "neuron"),
            'r': os.path.join(tmpdir, 'R'),
        }
        for example_project in list(example_projects.values()):
            assert os.path.exists(example_project)
            sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
        
    def test__find_dependencies_for_a_NEURON_project(self):
        deps = df.find_dependencies(os.path.join(tmpdir, "neuron", "main.hoc"),
                                    MockExecutable("NEURON"))
        self.assertEqual(os.path.basename(deps[0].path), "dependency.hoc")

    @unittest.skipIf(skip_ci, "Skipping test on CI server")
    def test__find_dependencies_for_R_project(self):
        deps = df.find_dependencies(os.path.join(tmpdir, "R", "myscript.R"),
                                    MockRExecutable("R"))
        self.assertEqual(len(deps), 2)

    def test__find_dependencies_with_unsupported_executable__should_raise_warning(self):
        warnings.filters.append(('error', None, UserWarning, None, 0)) # ought to remove this again afterwards
        self.assertRaises(UserWarning,
                          df.find_dependencies,
                          os.path.join(tmpdir, "python", "main.py"),
                          MockExecutable("Perl")) # I'm not saying Perl shouldn't be supported, it just isn't at present
        

class TestPythonDependency(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        self.example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(self.example_project)
        sys.path.append(os.path.abspath(self.example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__init(self):
        dep = df.python.Dependency("main", os.path.join(self.example_project, "main.py"), version="1.2.3b")
        self.assertEqual(dep.version, "1.2.3b")

    @unittest.skipUnless(have_numpy, "test requires NumPy")
    def test__from_module(self):
        dep = df.python.Dependency.from_module(sys.modules['numpy'], None)
        self.assertEqual(dep.name, "numpy")

    def test__str(self):
        dep = df.python.Dependency("main", "/some/path")
        str(dep)
        
    def test_eq(self):
        path = os.path.join(self.example_project, "main.py")
        dep1 = df.python.Dependency("main", path)
        dep2 = df.python.Dependency("main", path)
        self.assertEqual(dep1, dep2)

    def test_ne(self):
        path = "/some/path"
        dep1 = df.python.Dependency("main", path)
        dep2 = df.python.Dependency("unittest", path)
        self.assertNotEqual(dep1, dep2)


class TestNEURONDependency(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        self.example_project = os.path.join(tmpdir, "neuron")
        assert os.path.exists(self.example_project)
        sys.path.append(os.path.abspath(self.example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__init(self):
        dep = df.neuron.Dependency(os.path.join(self.example_project, "main.hoc"))
        self.assertEqual(dep.version, "unknown")

    def test__str(self):
        dep = df.neuron.Dependency(os.path.join(self.example_project, "main.hoc"))
        str(dep)
        
    def test_eq(self):
        dep1 = df.neuron.Dependency(os.path.join(self.example_project, "main.hoc"))
        dep2 = df.neuron.Dependency(os.path.join(self.example_project, "main.hoc"))
        self.assertEqual(dep1, dep2)

    def test_ne(self):
        dep1 = df.neuron.Dependency(os.path.join(self.example_project, "main.hoc"))
        dep2 = df.neuron.Dependency(os.path.join(self.example_project, "dependency.hoc"))
        self.assertNotEqual(dep1, dep2)

class TestRDependency(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        self.example_project = os.path.join(tmpdir, "R")
        assert os.path.exists(self.example_project)
        sys.path.append(os.path.abspath(self.example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__init(self):
        dep = df.r.Dependency(os.path.join(self.example_project, "myscript.R"))
        self.assertEqual(dep.version, "unknown")

    def test__str(self):
        dep = df.r.Dependency(os.path.join(self.example_project, "myscript.R"))
        str(dep)
        
    def test_eq(self):
        dep1 = df.r.Dependency(os.path.join(self.example_project, "myscript.R"))
        dep2 = df.r.Dependency(os.path.join(self.example_project, "myscript.R"))
        self.assertEqual(dep1, dep2)

    def test_ne(self):
        dep1 = df.r.Dependency(os.path.join(self.example_project, "myscript.R"))
        dep2 = df.r.Dependency(os.path.join(self.example_project, "myscript2.R"))
        self.assertNotEqual(dep1, dep2)


def setup():
    global tmpdir
    tmpdir = tempfile.mkdtemp()
    shutil.rmtree(tmpdir)
    this_directory = os.path.dirname(__file__)
    shutil.copytree(os.path.join(this_directory, os.path.pardir, "example_projects"), tmpdir)
    print(os.listdir(tmpdir))

def teardown():
    global tmpdir
    print("removing tmpdir")
    shutil.rmtree(tmpdir) # this only gets called when running with nose. Perhaps use atexit, or do this on a class-by-class basis and use __del__


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
    
