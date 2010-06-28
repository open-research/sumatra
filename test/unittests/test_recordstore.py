"""
Unit tests for the sumatra.recordstore package
"""

import unittest
import os
import sys
from datetime import datetime
from django.core import management
from sumatra.records import SimRecord
from sumatra.programs import register_executable, Executable
from sumatra.recordstore.shelve_store import ShelveRecordStore
from sumatra.recordstore.django_store import DjangoRecordStore
from sumatra.recordstore.http_store import HttpRecordStore
from sumatra.versioncontrol import vcs_list
import sumatra.launch
import sumatra.datastore

class MockExecutable(Executable):
    name = "a.out"
    path = "/usr/local/bin/a.out"
    version = "999"
    def __init__(self, *args, **kwargs):
        pass
register_executable(MockExecutable, "a.out", "/usr/local/bin/a.out", [])

class MockRepository(object):
    url = "http://svn.example.com/"
    type = "MockRepository"
    def __init__(self, *args, **kwargs):
        pass
vcs_list.append(sys.modules[__name__])

class MockLaunchMode(object):
    type = "SerialLaunchMode"
    def get_state(self):
        return {}
sumatra.launch.MockLaunchMode = MockLaunchMode

class MockDataStore(object):
    type = "FileSystemDataStore"
    def __init__(self, **parameters):
        pass
    def get_state(self):
        return {'root': "/tmp"}
sumatra.datastore.MockDataStore = MockDataStore

class MockDependency(object):
    name = "some_module"
    path = "/usr/lib/python/some_module.py"
    version = "1.0"
    diff = ""
    module = "python"
    
class MockPlatformInformation(object):
    architecture_bits = 32
    architecture_linkage = ""
    machine = ""
    network_name = ""
    ip_addr = "192.168.0.0"
    processor = ""
    release = ""
    system_name = ""
    version = ""

class MockRecord(object):
    
    def __init__(self, timestamp, group="default"):
        self.group = group
        self.timestamp = timestamp
        self.reason = "because"
        self.duration = 7543.2
        self.outcome = None
        self.main_file = "test"
        self.version = "99863a9dc5f"
        self.data_key = "[]"
        self.executable = MockExecutable()
        self.repository = MockRepository()
        self.launch_mode = MockLaunchMode()
        self.datastore = MockDataStore()
        self.parameters = {}
        self.tags = set([])
        self.dependencies = [MockDependency(), MockDependency()]
        self.platforms = [MockPlatformInformation()]
        self.diff = ""
        self.user = "michaelpalin"
        
    @property
    def label(self):
        return "%s_%s" % (self.group, self.timestamp.strftime("%Y%m%d-%H%M%S"))

class MockProject(object):
    name = "TestProject"


class BaseTestRecordStore(object):
    
    def add_some_records(self):
        r1 = MockRecord(timestamp=datetime(2009, 1, 1), group="groupA")
        r2 = MockRecord(timestamp=datetime(2009, 1, 2), group="groupA")
        r3 = MockRecord(timestamp=datetime(2009, 1, 2), group="groupB")
        for r in r1, r2, r3:
            print "saving record %s" % r.label
            self.store.save(self.project.name, r)

    def add_some_tags(self):
        r1 = MockRecord(timestamp=datetime(2009, 1, 1), group="groupA")
        r3 = MockRecord(timestamp=datetime(2009, 1, 2), group="groupB")
        r1.tags.add("tag1")
        r1.tags.add("tag2")
        r3.tags.add("tag1")
        self.store.save(self.project.name, r1)
        self.store.save(self.project.name, r3)

    def test_create_record_store_should_not_produce_errors(self):
        pass
    
    def test_save_should_not_produce_errors(self):
        self.add_some_records()
    
    def test_get(self):
        self.add_some_records()
        r = self.store.get(self.project.name, "groupA_20090101-000000")
        assert isinstance(r, (MockRecord, SimRecord)), type(r)
        assert r.label == "groupA_20090101-000000", r.label
        
    def test_get_nonexistent_record_raises_KeyError(self):
        self.assertRaises(KeyError, self.store.get, self.project.name, "foo")

    def test_list_without_groups_should_return_all_records(self):
        self.add_some_records()
        records = self.store.list(self.project.name, [])
        assert isinstance(records, list)
        self.assertEqual(len(records), 3)
        
    def test_list_with_groups_should_return_subset_of_records(self):
        self.add_some_records()
        records = self.store.list(self.project.name, ["groupA"])
        assert len(records) == 2
        for record in records:
            assert record.group == "groupA"
        records = self.store.list(self.project.name, ["groupA", "groupB", "foo"])
        assert len(records) == 3
        
    def test_delete_removes_record(self):
        self.add_some_records()
        key = "groupA_20090101-000000"
        self.store.delete(self.project.name, key)
        self.assertRaises(KeyError, self.store.get, self.project.name, key)

    def test_delete_group(self):
        self.add_some_records()
        assert self.store.delete_group(self.project.name, "groupA") == 2
        self.assertEqual(len(self.store.list(self.project.name, ["groupA"])), 0)

    def test_delete_by_tag(self):
        self.add_some_records()
        self.assertEqual(len(self.store.list(self.project.name, [])), 3)
        self.add_some_tags()
        r = self.store.get(self.project.name, "groupA_20090101-000000")
        self.assertEqual(r.tags, set(['tag1', 'tag2']))
        n = self.store.delete_by_tag(self.project.name, "tag1")
        self.assertEqual(n, 2)
        self.assertEqual(len(self.store.list(self.project.name, [])), 1)
        self.assertRaises(KeyError, self.store.get, self.project.name, "groupA_20090101-000000")

    def test_str(self):
        #this test is pointless, just to increase coverage
        assert isinstance(str(self.store), basestring)


class TestShelveRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    
    def setUp(self):
        self.store = ShelveRecordStore(shelf_name="test_record_store")
        self.project = MockProject()
        
    def tearDown(self):
        os.remove("test_record_store")

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        unpickled = pickle.loads(s)
        assert unpickled._shelf_name == "test_record_store"
        assert os.path.exists(unpickled._shelf_name)

    



class TestDjangoRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    def setUp(self):
        self.store = DjangoRecordStore(db_file="test_record_store.db")
        self.project = MockProject()

    def tearDown(self):
        management.call_command("reset", "django_store", interactive=False)

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        unpickled = pickle.loads(s)
        #assert unpickled._shelf_name == "test_record_store"
        #assert os.path.exists(unpickled._shelf_name)


class TestHttpRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    def setUp(self):
        self.store = HttpRecordStore("http://127.0.0.1:8000/records/", "testuser", "z6Ty49HY")
        self.project = MockProject()
        
    def tearDown(self):
        pass
    
    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        unpickled = pickle.loads(s)


if __name__ == '__main__':
    if os.path.exists("test_record_store.db"):
        os.remove("test_record_store.db")
    unittest.main()
    