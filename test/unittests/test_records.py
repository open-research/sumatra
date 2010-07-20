"""
Unit tests for the sumatra.records module
"""

import unittest
import time
from sumatra.records import Record, RecordDifference


class MockExecutable(object):
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return not self.__eq__(other)
    
class MockRepository(object):
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return not self.__eq__(other)

class MockLaunchMode(object):
    pass

class MockFile(object):
    def __init__(self, name):
        self.name = name
        self.mimetype = "/application/foo"
        self.content = "afdbceg"
        self.sorted_content = "abcdefg"
        self.size = len(self.content)
    def __eq__(self, other):
        if self.size != other.size:
            return False
        elif self.content == other.content:
            return True
        else:
            return self.sorted_content == other.sorted_content    
    def __ne__(self, other):
        return not self.__eq__(other)

class MockDataStore(object):
    def list_files(self, key):
        return [MockFile("1.dat"), MockFile("2.dat")]
    def copy(self):
        return self

class MockDependency(object):
    def __init__(self, name):
        self.name = name
        

class TestRecord(unittest.TestCase):
    pass

class TestRecordDifference(unittest.TestCase):
    
    def test__init(self):
        r1 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        time.sleep(1)
        r2 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        diff = RecordDifference(r1, r2)
        
    def test__nonzero__should_return_True__for_different_parameters(self):
        r1 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore(), {"a": 2})
        time.sleep(1)
        r2 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore(), {"a": 3}, )
        r1.dependencies = []
        r2.dependencies = []
        diff = RecordDifference(r1, r2)
        self.assertEqual(diff.executable_differs, False)
        self.assertEqual(diff.code_differs, False)
        self.assertEqual(diff.parameters_differ, True)
        self.assertEqual(diff.data_differs, False)
        assert diff.__nonzero__()
        
    def test__nonzero__should_return_True__for_identical_parameters(self):
        r1 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore(), {"a": 2})
        time.sleep(1)
        r2 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore(), {"a": 2})
        r1.dependencies = []
        r2.dependencies = []
        diff = RecordDifference(r1, r2)
        self.assertEqual(diff.executable_differs, False)
        self.assertEqual(diff.code_differs, False)
        self.assertEqual(diff.parameters_differ, False)
        self.assertEqual(diff.data_differs, False)
        self.assertEqual(diff.__nonzero__(), False)

    def test__dependency_differences(self):
        r1 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        time.sleep(1)
        r2 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        r1.dependencies = [MockDependency("foo"), MockDependency("bar")]
        r2.dependencies = [MockDependency("bar"), MockDependency("eric")]
        diff = RecordDifference(r1, r2)
        diff.dependency_differences

    def test__data_differences(self):
        r1 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        time.sleep(1)
        r2 = Record(MockExecutable(), MockRepository(), "test.py",
                       999, MockLaunchMode(), MockDataStore())
        diff = RecordDifference(r1, r2)
        diff.data_differences

if __name__ == '__main__':
    unittest.main()
