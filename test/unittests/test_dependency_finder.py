"""
Unit tests for the sumatra.dependency_finder module
"""

import unittest
import sumatra.dependency_finder as df
import sys
import os
import numpy


class MockExecutable(object):
    def __init__(self, name):
        self.name = name
                

class TestModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_project = os.path.join(os.path.pardir, "example_project")
        assert os.path.exists(example_project)
        sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__find_version_by_attribute(self):
        import main
        self.assertEqual(df.find_version_by_attribute(main), "1.2.3b")
        del main.get_version
        self.assertEqual(df.find_version_by_attribute(main), "1.2.3a")
        
    def test__find_version_from_egg(self):
        import main
        self.assertEqual(df.find_version_from_egg(main), "1.2.3egg")
    
    def test__find_version(self):
        import main
        self.assertEqual(df.find_version(main), "1.2.3b")
    
    def test__find_imported_packages(self):
        # the example project has numpy as its only import
        example_project_imports = df.find_imported_packages(os.path.join(os.path.pardir, "example_project", "main.py"))
        assert "numpy" in example_project_imports.keys()
        numpy_imports = df.find_imported_packages(numpy.__file__.replace(".pyc", ".py"))
        assert len(example_project_imports) == len(numpy_imports)
        for key in numpy_imports:
            self.assertEqual(str(numpy_imports[key]),
                             str(example_project_imports[key]))
    
    def test_find_dependencies(self):
        df.find_dependencies(os.path.join(os.path.pardir, "example_project", "main.py"),
                             MockExecutable("Python"))
        
    def test__find_dependencies_with_unsupported_executable__should_raise_exception(self):
        self.assertRaises(Exception,
                          df.find_dependencies,
                          os.path.join(os.path.pardir, "example_project", "main.py"),
                          MockExecutable("Perl"))
        
    def test__run_builtin_tests(self):
        df.test()


class TestDependency(unittest.TestCase):
    
    def setUp(self):
        self.saved_path = sys.path[:]
        example_project = os.path.join(os.path.pardir, "example_project")
        assert os.path.exists(example_project)
        sys.path.append(os.path.abspath(example_project))
    
    def tearDown(self):
        sys.path = self.saved_path
    
    def test__init(self):
        dep = df.Dependency("main")
        self.assertEqual(dep.version, "1.2.3b")

    def test__str(self):
        dep = df.Dependency("main")
        str(dep)
        
    def test_eq(self):
        dep1 = df.Dependency("main")
        dep2 = df.Dependency("main")
        self.assertEqual(dep1, dep2)

    def test_ne(self):
        dep1 = df.Dependency("main")
        dep2 = df.Dependency("unittest")
        self.assertNotEqual(dep1, dep2)
        
    def test__init__with_nonexistent_module(self):
        dep = df.Dependency("foo")
        assert isinstance(dep.import_error, ImportError)
        assert dep.version == 'unknown'
        
        
if __name__ == '__main__':
    unittest.main()