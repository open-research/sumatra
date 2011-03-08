"""
Unit tests for the sumatra.recordstore package
"""

import unittest2 as unittest
import os
import sys
from datetime import datetime
from django.core import management

from sumatra.records import Record
from sumatra.programs import register_executable, Executable
from sumatra.recordstore import shelve_store, django_store, http_store
from sumatra.versioncontrol import vcs_list
import sumatra.launch
import sumatra.datastore
import sumatra.parameters
try:
    import json
except ImportError:
    import simplejson as json
import urlparse
    
originals = []

class MockExecutable(Executable):
    name = "a.out"
    path = "/usr/local/bin/a.out"
    version = "999"
    options = "-v"
    def __init__(self, *args, **kwargs):
        pass
register_executable(MockExecutable, "a.out", "/usr/local/bin/a.out", [])

class MockRepository(object):
    url = "http://svn.example.com/"
    type = "MockRepository"
    def __init__(self, *args, **kwargs):
        pass
vcs_list.append(sys.modules[__name__])

def tearDownModule():
    vcs_list.remove(sys.modules[__name__])

class MockLaunchMode(object):
    type = "SerialLaunchMode"
    def __getstate__(self):
        return {}

class MockDataStore(object):
    type = "FileSystemDataStore"
    def __init__(self, **parameters):
        pass
    def __getstate__(self):
        return {'root': "/tmp"}
    def copy(self):
        return self

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

class MockParameterSet(object):
    def __init__(self, initialiser):
        pass
    def as_dict(self):
        return {}

class MockRecord(object):
    
    def __init__(self, label):
        self.label = label
        self.timestamp = datetime.now() #datetime(1901, 6, 1, 12, 0, 0)
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
        self.parameters = MockParameterSet({})
        self.tags = set([])
        self.dependencies = [MockDependency(), MockDependency()]
        self.platforms = [MockPlatformInformation()]
        self.diff = ""
        self.user = "michaelpalin"
        self.input_data = "[]"
        self.script_arguments = "arg1 arg2"

class MockProject(object):
    name = "TestProject"

def clean_up():
    if os.path.exists("test_record_store.db"):
        os.remove("test_record_store.db")

def setup():
    clean_up()
    sumatra.launch.MockLaunchMode = MockLaunchMode
    sumatra.datastore.MockDataStore = MockDataStore
    sumatra.parameters.MockParameterSet = MockParameterSet

def teardown():
    del sumatra.launch.MockLaunchMode
    del sumatra.datastore.MockDataStore
    del sumatra.parameters.MockParameterSet


class BaseTestRecordStore(object):
    
    def add_some_records(self):
        r1 = MockRecord("record1")
        r2 = MockRecord("record2")
        r3 = MockRecord("record3")
        for r in r1, r2, r3:
            #print "saving record %s" % r.label
            self.store.save(self.project.name, r)

    def add_some_tags(self):
        r1 = MockRecord("record1")
        r3 = MockRecord("record3")
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
        r = self.store.get(self.project.name, "record1")
        assert isinstance(r, (MockRecord, Record)), type(r)
        assert r.label == "record1", r.label
        
    def test_get_nonexistent_record_raises_KeyError(self):
        self.assertRaises(KeyError, self.store.get, self.project.name, "foo")

    def test_list_without_tags_should_return_all_records(self):
        self.add_some_records()
        records = self.store.list(self.project.name)
        assert isinstance(records, list), type(records)
        self.assertEqual(len(records), 3)
    
    def test_list_for_tags_should_filter_records_appropriately(self):
        self.add_some_records()
        self.add_some_tags()
        records = self.store.list(self.project.name, "tag1")
        self.assertEqual(len(records), 2)
    
    def test_delete_removes_record(self):
        self.add_some_records()
        key = "record1"
        self.store.delete(self.project.name, key)
        self.assertRaises(KeyError, self.store.get, self.project.name, key)

    def test_delete_by_tag(self):
        self.add_some_records()
        self.assertEqual(len(self.store.list(self.project.name)), 3)
        self.add_some_tags()
        r = self.store.get(self.project.name, "record1")
        self.assertEqual(r.tags, set(['tag1', 'tag2']))
        n = self.store.delete_by_tag(self.project.name, "tag1")
        self.assertEqual(n, 2)
        self.assertEqual(len(self.store.list(self.project.name)), 1)
        self.assertRaises(KeyError, self.store.get, self.project.name, "record1")

    def test_str(self):
        #this test is pointless, just to increase coverage
        assert isinstance(str(self.store), basestring)

    def test_most_recent(self):
        self.add_some_records()
        self.assertEqual(self.store.most_recent(self.project.name), "record3")
        self.store.delete(self.project.name, "record3")
        self.assertEqual(self.store.most_recent(self.project.name), "record2")


class TestShelveRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    
    def setUp(self):
        self.store = shelve_store.ShelveRecordStore(shelf_name="test_record_store")
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
        self.store = django_store.DjangoRecordStore(db_file="test.db")
        self.project = MockProject()

    def tearDown(self):
        management.call_command("reset", "django_store", interactive=False)

    def __del__(self):
        clean_up()

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        unpickled = pickle.loads(s)
        #assert unpickled._shelf_name == "test_record_store"
        #assert os.path.exists(unpickled._shelf_name)


class MockResponse(object):
    def __init__(self, status):
        self.status = status

def check_record(record):
    # this is a rather basic test. Should also check the keys of the
    # subsidiary dicts, and the types of the values
    assert set(record.keys()) == set(["executable", "parameters", "repository",
                                      "tags", "main_file", "label", "platforms",
                                      "reason", "version", "user", "launch_mode",
                                      "timestamp", "duration", "diff",
                                      "datastore", "outcome", "data_key",
                                      "dependencies", "input_data",
                                      "script_arguments"])

class MockCredentials(object):
        credentials = [['domain', 'username', 'password']]

class MockHttp(object):
    def __init__(self, *args):
        self.records = {}
        self.debug = False
        self.last_record = None
        self.credentials = MockCredentials()
    def add_credentials(self, *args, **kwargs):
        pass
    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        u = urlparse.urlparse(uri)
        parts = u.path.split("/")[1:-1]
        if self.debug:
            print "\n<<<<<", uri, u.path, len(parts), method, body, headers, u.params, u.query
        if len(parts) == 2: # record uri
            if method == "PUT":
                record = json.loads(body)
                check_record(record)
                self.records[parts[1]] = record
                content = ""
                status = 200
                self.last_record = record
            elif method == "GET":
                label = parts[1]
                if label == "last":
                    content = json.dumps(self.last_record)
                else:
                    content = json.dumps(self.records[label])
                status = 200
            elif method == "DELETE":
                self.records.pop(parts[1])
                most_recent = u""
                for record in self.records.itervalues():
                    if record["timestamp"] > most_recent:
                        most_recent = record["timestamp"]
                        self.last_record = record
                content = ""
                status = 204
        elif len(parts) == 1: # project uri
            if u.query:
                tags = u.query.split("=")[1].split(",")
                records = set([])
                for tag in tags:
                    records = records.union(["%s://%s/%s/%s/" % (u.scheme, u.netloc, parts[0],
                                               path) for path in self.records.keys() if tag in self.records[path]['tags']])
                records = list(records)
            else:
                records = ["%s://%s/%s/%s/" % (u.scheme, u.netloc, parts[0],
                                                    path) for path in self.records.keys()]
            content = json.dumps({"records": records})
            status = 200
        elif len(parts) == 3: # tagged records uri
            if method == "DELETE":
                tag = parts[2]
                n = 0
                for key, record in self.records.items():
                    if tag in record["tags"]:
                        self.records.pop(key)
                        n += 1
                status = 200
                content = str(n)
        if self.debug:
            print ">>>>>", status, content
        return MockResponse(status), content
    

class MockHttpLib(object):
    
    @staticmethod
    def Http(*args):
        return MockHttp(*args)


class TestHttpRecordStore(unittest.TestCase, BaseTestRecordStore):
    
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.real_httplib = http_store.httplib2
        http_store.httplib2 = MockHttpLib()
        
    def __del__(self):
        http_store.httplib2 = self.real_httplib
    
    def setUp(self):
        self.store = http_store.HttpRecordStore("http://127.0.0.1:8000/", "testuser", "z6Ty49HY")
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
    setup()
    unittest.main()
    teardown()
