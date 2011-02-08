"""
Unit tests for the sumatra.dependency_finder module
"""

import unittest
import sumatra.dependency_finder as df
import sys
import os
import numpy
import tempfile
import shutil
import warnings

class MockExecutable(object):
    def __init__(self, name):
        self.name = name
        self.path = name
                

class TestPythonModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(example_project)
        sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__find_version_by_attribute(self):
        import main
        self.assertEqual(df.python.find_version_by_attribute(main), "1.2.3b")
        del main.get_version
        self.assertEqual(df.python.find_version_by_attribute(main), "1.2.3a")
        
    def test__find_version_from_egg(self):
        import main
        self.assertEqual(df.python.find_version_from_egg(main), "1.2.3egg")
    
    def test__find_imported_packages(self):
        # the example project has numpy as its only import
        example_project_imports = df.python.find_imported_packages(os.path.join(tmpdir, "python", "main.py"))
        assert "numpy" in example_project_imports.keys()
        numpy_imports = df.python.find_imported_packages(numpy.__file__.replace(".pyc", ".py"))
        assert len(example_project_imports) == len(numpy_imports)
        for key in numpy_imports:
            self.assertEqual(str(numpy_imports[key]),
                             str(example_project_imports[key]))    
    

class TestCoreModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(example_project)
        sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
        
    def test__find_version(self):
        import main
        self.assertEqual(df.core.find_version(main, df.python.heuristics), "1.2.3b")
        
        
class TestMainModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_projects = {
            'python': os.path.join(tmpdir, "python"),
            'neuron': os.path.join(tmpdir, "neuron"),
        }
        for example_project in example_projects.values():
            assert os.path.exists(example_project)
            sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
        
    def test__find_dependencies_for_a_NEURON_project(self):
        deps = df.find_dependencies(os.path.join(tmpdir, "neuron", "main.hoc"),
                                    MockExecutable("NEURON"))
        self.assertEqual(os.path.basename(deps[0].path), "dependency.hoc")  
        
    def test__find_dependencies_with_unsupported_executable__should_raise_warning(self):
        warnings.filters.append(('error', None, UserWarning, None, 0)) # ought to remove this again afterwards
        self.assertRaises(UserWarning,
                          df.find_dependencies,
                          os.path.join(tmpdir, "python", "main.py"),
                          MockExecutable("Perl")) # I'm not saying Perl shouldn't be supported, it just isn't at present
        

class TestPythonDependency(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_project = os.path.join(tmpdir, "python")
        assert os.path.exists(example_project)
        sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__init(self):
        dep = df.python.Dependency("main")
        self.assertEqual(dep.version, "1.2.3b")

    def test__str(self):
        dep = df.python.Dependency("main")
        str(dep)
        
    def test_eq(self):
        dep1 = df.python.Dependency("main")
        dep2 = df.python.Dependency("main")
        self.assertEqual(dep1, dep2)

    def test_ne(self):
        dep1 = df.python.Dependency("main")
        dep2 = df.python.Dependency("unittest")
        self.assertNotEqual(dep1, dep2)
        
    def test__init__with_nonexistent_module(self):
        dep = df.python.Dependency("foo")
        assert isinstance(dep.import_error, ImportError)
        assert dep.version == 'unknown'
        
        
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
        
    def test__init__with_nonexistent_path(self):
        self.assertRaises(IOError, df.neuron.Dependency, "foo.hoc")

def setup():
    global tmpdir
    tmpdir = tempfile.mkdtemp()
    shutil.rmtree(tmpdir)
    shutil.copytree(os.path.join(os.path.pardir, "example_projects"), tmpdir)
    print os.listdir(tmpdir)

def teardown():
    global tmpdir
    print "removing tmpdir"
    shutil.rmtree(tmpdir) # this only gets called when running with nose. Perhaps use atexit, or do this on a class-by-class basis and use __del__


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
    
