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
from sumatra.versioncontrol import vcs_list

class MockExecutable(Executable):
    name = "a.out"
    path = "/usr/local/bin/a.out"
    version = 999
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

class MockDataStore(object):
    type = "FileSystemDataStore"
    def get_state(self):
        return {'root': "/tmp"}

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
        self.duration = 7543
        self.outcome = None
        self.main_file = "test"
        self.version = "99863a9dc5f"
        self.data_key = "[]"
        self.executable = MockExecutable()
        self.repository = MockRepository()
        self.launch_mode = MockLaunchMode()
        self.datastore = MockDataStore()
        self.parameters = {}
        self.tags = []
        self.dependencies = [MockDependency(), MockDependency()]
        self.platforms = [MockPlatformInformation()]
        self.diff = ""
        
    @property
    def label(self):
        return "%s_%s" % (self.group, self.timestamp.strftime("%Y%m%d-%H%M%S"))


class BaseTestRecordStore(object):
    
    def add_some_records(self):
        r1 = MockRecord(timestamp=datetime(2009, 1, 1), group="groupA")
        r2 = MockRecord(timestamp=datetime(2009, 1, 2), group="groupA")
        r3 = MockRecord(timestamp=datetime(2009, 1, 2), group="groupB")
        for r in r1, r2, r3:
            self.store.save(r)

    def test_create_record_store_should_not_produce_errors(self):
        pass
    
    def test_save_should_not_produce_errors(self):
        self.add_some_records()
    
    def test_get(self):
        self.add_some_records()
        r = self.store.get("groupA_20090101-000000")
        assert isinstance(r, (MockRecord, SimRecord)), type(r)
        assert r.label == "groupA_20090101-000000", r.label
        
    def test_get_nonexistent_record_raises_KeyError(self):
        self.assertRaises(KeyError, self.store.get, "foo")

    def test_list_without_groups_should_return_all_records(self):
        self.add_some_records()
        records = self.store.list([])
        assert isinstance(records, list)
        assert len(records) == 3
        
    def test_list_with_groups_should_return_subset_of_records(self):
        self.add_some_records()
        records = self.store.list(["groupA"])
        assert len(records) == 2
        for record in records:
            assert record.group == "groupA"
        records = self.store.list(["groupA", "groupB", "foo"])
        assert len(records) == 3
        
    def test_delete_removes_record(self):
        self.add_some_records()
        key = "groupA_20090101-000000"
        self.store.delete(key)
        self.assertRaises(KeyError, self.store.get, key)

    def test_delete_group(self):
        self.add_some_records()
        assert self.store.delete_group("groupA") == 2
        assert len(self.store.list(["groupA"])) == 0

    def test_str(self):
        #this test is pointless, just to increase coverage
        assert isinstance(str(self.store), basestring)

class TestShelveRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    
    def setUp(self):
        self.store = ShelveRecordStore(shelf_name="test_record_store")
        
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


if __name__ == '__main__':
    if os.path.exists("test_record_store.db"):
        os.remove("test_record_store.db")
    unittest.main()
    