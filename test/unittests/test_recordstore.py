"""
Unit tests for the sumatra.recordstore package
"""

from __future__ import unicode_literals
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from glob import glob

from sumatra.records import Record
from sumatra.programs import Executable
from sumatra.recordstore import (shelve_store, django_store, http_store,
                                 serialization, get_record_store)
from sumatra.versioncontrol import vcs_list
import sumatra.launch
import sumatra.datastore
import sumatra.parameters
from sumatra.core import component
import json
import urllib.parse


originals = []
django_store1 = None
django_store2 = None
django_dir = None

this_directory = os.path.dirname(__file__)


@component
class MockExecutable(Executable):
    name = "a.out"
    executable_names = ("/usr/local/bin/a.out",)
    file_extensions = []
    path = "/usr/local/bin/a.out"
    version = "999"
    options = "-v"
    def __init__(self, *args, **kwargs):
        pass


class MockRepository(object):
    url = "http://svn.example.com/"
    upstream = None
    type = "MockRepository"
    def __init__(self, *args, **kwargs):
        pass


class MockLaunchMode(object):
    type = "SerialLaunchMode"
    def __getstate__(self):
        return {}


class MockDataStore(object):
    type = "FileSystemDataStore"
    def __init__(self, **parameters):
        self.root = parameters.get("root", None) or "/tmp"
    def __getstate__(self):
        return {'root': self.root}
    def copy(self):
        return self


class MockDependency(object):
    name = "some_module"
    path = "/usr/lib/python/some_module.py"
    version = "1.0"
    diff = ""
    module = "python"
    source = "http://git.example.com/"


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
    def pop(self, k, d):
        return None


class MockRecord(object):

    def __init__(self, label, timestamp=datetime.now()):
        self.label = label
        self.timestamp = timestamp
        self.reason = "because"
        self.duration = 7543.2
        self.outcome = None
        self.stdout_stderr = "ok"
        self.main_file = "test"
        self.version = "99863a9dc5f"
        self.output_data = []
        self.executable = MockExecutable()
        self.repository = MockRepository()
        self.launch_mode = MockLaunchMode()
        self.datastore = MockDataStore()
        self.input_datastore = MockDataStore()
        self.parameters = MockParameterSet({})
        self.tags = set([])
        self.dependencies = [MockDependency(), MockDependency()]
        self.platforms = [MockPlatformInformation()]
        self.diff = ""
        self.user = "michaelpalin"
        self.input_data = []
        self.script_arguments = "arg1 arg2"
        self.repeats = None

    def __eq__(self, other):
        return self.label == other.label and self.duration == other.duration


class MockProject(object):
    name = "TestProject"


def setup():
    global django_store1, django_store2, django_dir
    django_dir = tempfile.mkdtemp(prefix='sumatra-test-')
    cwd_before = os.getcwd()
    os.chdir(django_dir)
    sumatra.launch.MockLaunchMode = MockLaunchMode
    sumatra.datastore.MockDataStore = MockDataStore
    sumatra.parameters.MockParameterSet = MockParameterSet
    if django_store1 is None:
        django_store1 = django_store.DjangoRecordStore(db_file="test.db")
    if django_store2 is None:
        django_store2 = django_store.DjangoRecordStore(db_file="test2.db")
    django_store.db_config.configure()
    vcs_list.append(sys.modules[__name__])
    os.chdir(cwd_before)


def teardown():
    global django_store1, django_store2, django_dir
    del sumatra.launch.MockLaunchMode
    del sumatra.datastore.MockDataStore
    del sumatra.parameters.MockParameterSet
    shutil.rmtree(django_dir)
    vcs_list.remove(sys.modules[__name__])


class BaseTestRecordStore(object):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='sumatra-test-')
        self.cwd_before_test = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        django_store1.delete_all()
        django_store2.delete_all()
        os.chdir(self.cwd_before_test)
        shutil.rmtree(self.dir)

    def add_some_records(self):
        # records must have a delta timestamp of one second as RecordStores
        # might serialize the record using serialization.encode_record
        # (like HttpRecordStore). There, the timestamp will be cut off
        # milliseconds.
        now = datetime.now()
        r1 = MockRecord("record1", timestamp=now - timedelta(seconds=2))
        r2 = MockRecord("record2", timestamp=now - timedelta(seconds=1))
        r3 = MockRecord("record3", timestamp=now)
        for r in r1, r2, r3:
            #print "saving record %s" % r.label
            self.store.save(self.project.name, r)

    def add_some_tags(self):
        # records must have a delta timestamp of one second as RecordStores
        # might serialize the record using serialization.encode_record
        # (like HttpRecordStore). There, the timestamp will be cut off
        # milliseconds.
        now = datetime.now()
        r1 = MockRecord("record1", timestamp=now - timedelta(seconds=1))
        r3 = MockRecord("record3", timestamp=now)
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

    def test_delete_nonexistent_label(self):
        self.add_some_records()
        self.assertRaises(Exception,  # could be KeyError or DoesNotExist
                          self.store.delete,
                          self.project.name,
                          "notarecord")
        # should emit warning but not exception

    def test_str(self):
        #this test is pointless, just to increase coverage
        assert isinstance(str(self.store), str)

    def test_most_recent(self):
        self.add_some_records()
        self.assertEqual(self.store.most_recent(self.project.name), "record3")
        self.store.delete(self.project.name, "record3")
        self.assertEqual(self.store.most_recent(self.project.name), "record2")

    def test_sync_with_shelve_store(self):
        self.add_some_records()
        other_store = shelve_store.ShelveRecordStore(shelf_name="test_record_store2")
        self.assertEqual(len(other_store.list(self.project.name)), 0)
        self.store.sync(other_store, self.project.name)
        self.assertEqual(sorted(rec.label for rec in self.store.list(self.project.name)),
                         sorted(rec.label for rec in other_store.list(self.project.name)))

    def test_sync_with_django_store(self):
        other_store = django_store2
        self.add_some_records()
        self.assertEqual(len(other_store.list(self.project.name)), 0)
        self.store.sync(other_store, self.project.name)
        self.assertEqual(sorted(rec.label for rec in self.store.list(self.project.name)),
                         sorted(rec.label for rec in other_store.list(self.project.name)))

    def test_update(self):
        self.add_some_records()
        self.store.update(self.project.name, "datastore.root", "/new/path/to/store")
        updated_value, = set(rec.datastore.root for rec in self.store.list(self.project.name))
        self.assertEqual(updated_value, "/new/path/to/store")

    def test_clear(self):
        self.add_some_records()
        self.store.clear()


class TestShelveRecordStore(unittest.TestCase, BaseTestRecordStore):

    def setUp(self):
        BaseTestRecordStore.setUp(self)
        self.store = shelve_store.ShelveRecordStore(shelf_name="test_record_store")
        self.project = MockProject()

    def tearDown(self):
        del self.store  # this is necessary when using the dumbdbm module, which otherwise creates files after test
        BaseTestRecordStore.tearDown(self)

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        self.store = pickle.loads(s)
        self.assertEqual(self.store._shelf_name, "test_record_store")


class TestDjangoRecordStore(unittest.TestCase, BaseTestRecordStore):

    def setUp(self):
        BaseTestRecordStore.setUp(self)
        self.store = django_store1
        self.project = MockProject()

    def tearDown(self):
        BaseTestRecordStore.tearDown(self)

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        django_store.db_config.configured = False
        django_store.db_config._settings['DATABASES'] = {}
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
                                      "datastore", "outcome", "output_data",
                                      "dependencies", "input_data",
                                      "script_arguments", "stdout_stderr",
                                      "input_datastore", "repeats"])

class MockCredentials(object):
        credentials = [['domain', 'username', 'password']]

class MockHttp(object):
    def __init__(self, *args, **kwargs):
        self.records = {}
        self.debug = False
        self.last_record = None
        self.credentials = MockCredentials()
    def add_credentials(self, *args, **kwargs):
        pass
    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        u = urllib.parse.urlparse(uri)
        parts = u.path.split("/")[1:-1]
        if self.debug:
            print("\n<<<<< %s %s %d %s %s %s %s %s" % (uri, u.path, len(parts),
                                                       method, body, headers,
                                                       u.params, u.query))

        if len(parts) == 2:  # record uri
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
                most_recent = ""
                for record in self.records.values():
                    if record["timestamp"] > most_recent:
                        most_recent = record["timestamp"]
                        self.last_record = record
                content = ""
                status = 204
        elif len(parts) == 1:  # project uri
            if method == "GET":
                if u.query:
                    tags = u.query.split("=")[1].split(",")
                    records = set([])
                    for tag in tags:
                        records = records.union(["%s://%s/%s/%s/" % (
                            u.scheme, u.netloc, parts[0], path)
                            for path in self.records.keys() if tag in self.records[path]['tags']])
                    records = list(records)
                else:
                    records = ["%s://%s/%s/%s/" % (u.scheme, u.netloc, parts[0], path)
                               for path in self.records.keys()]
                content = json.dumps({"records": records, "name": "TestProject", "description": ""})
                status = 200
            elif method == "PUT":
                content = ""
                status = 201
        elif len(parts) == 3:  # tagged records uri
            if method == "DELETE":
                tag = parts[2]
                n = 0
                for key, record in list(self.records.items()):
                    if tag in record["tags"]:
                        self.records.pop(key)
                        n += 1
                status = 200
                content = str(n)
        elif len(parts) == 0:  # list projects uri
            status = 200
            content = '[{"id": "TestProject"}]'
        if self.debug:
            print(">>>>> %s %s" % (status, content))
        return MockResponse(status), content


class MockHttpLib(object):

    @staticmethod
    def Http(*args, **kwargs):
        return MockHttp(*args, **kwargs)


class TestHttpRecordStore(unittest.TestCase, BaseTestRecordStore):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.real_httplib = http_store.httplib2
        http_store.httplib2 = MockHttpLib()

    def __del__(self):
        http_store.httplib2 = self.real_httplib

    def setUp(self):
        BaseTestRecordStore.setUp(self)
        self.store = http_store.HttpRecordStore("http://127.0.0.1:8000/", "testuser", "z6Ty49HY")
        self.project = MockProject()

    def tearDown(self):
        BaseTestRecordStore.tearDown(self)

    def test_record_store_is_pickleable(self):
        import pickle
        self.add_some_records()
        s = pickle.dumps(self.store)
        del self.store
        unpickled = pickle.loads(s)

    def test_process_url(self):
        url, username, password = http_store.process_url("http://foo:bar@example.com:8000/path/file.html")
        self.assertEqual(username, "foo")
        self.assertEqual(password, "bar")
        self.assertEqual(url, "http://example.com:8000/path/file.html")

    def test_list_projects(self):
        self.assertEqual(self.store.list_projects(), [self.project.name])

    def test_create_project(self):
        self.store.create_project("NewProject", "A new test project", "A long description")

    def test_project_info(self):
        self.assertEqual(self.store.project_info("TestProject")["name"], "TestProject")

    def test_clear(self):
        pass  # override base class test to avoid UserWarning


class TestSerialization(unittest.TestCase):
    maxDiff = None

    def test_build_record_v0p4(self):
        with open(os.path.join(this_directory, "example_0.4.json")) as fp:
            record = serialization.build_record(json.load(fp))
        self.assertEqual(record.label, "haggling")

    def test_build_record_v0p3(self):
        with open(os.path.join(this_directory, "example_0.3.json")) as fp:
            record = serialization.build_record(json.load(fp))
        self.assertEqual(record.label, "haggling")

    def test_build_record_v0p5(self):
        with open(os.path.join(this_directory,"example_0.5.json")) as fp:
            record = serialization.build_record(json.load(fp))
        self.assertEqual(record.label, "haggling")

    def test_build_record_v0p6(self):
        with open(os.path.join(this_directory, "example_0.6.json")) as fp:
            record = serialization.build_record(json.load(fp))
        self.assertEqual(record.label, "haggling")

    def test_round_trip(self):
        with open(os.path.join(this_directory, "example_0.7.json")) as fp:
            data_in = json.load(fp)
        record = serialization.build_record(data_in)
        data_out = json.loads(serialization.encode_record(record, indent=2))
        # tags in records are a set, hence have arbitrary order.
        self.assertTrue('tags' in data_out)
        data_in['tags'] = sorted(data_in['tags'])
        data_out['tags'] = sorted(data_out['tags'])
        self.assertEqual(data_in, data_out)

    def test_encode_project_info(self):
        serialization.encode_project_info("foo", "description of foo")


class TestModuleFunctions(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='sumatra-test-')
        self.cwd_before_test = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd_before_test)
        shutil.rmtree(self.dir)

    def test_get_record_store_http(self, ):
        self.assertIsInstance(get_record_store("http://records.example.com/"),
                              http_store.HttpRecordStore)

    def test_get_record_store_shelve(self):
        store = shelve_store.ShelveRecordStore(shelf_name="test_record_store.shelf")
        key = "foo".__str__()  # string wrapping is necessary for dumbdbm, which fails with unicode in Py2
        store.shelf[key] = "bar"
        store.shelf.sync()
        del store
        assert len(glob("test_record_store.shelf*")) > 0
        self.assertIsInstance(get_record_store("test_record_store.shelf"),
                              shelve_store.ShelveRecordStore)

    def test_get_record_store_create_shelve(self):
        assert len(glob("test_record_store.shelf*")) == 0
        self.assertIsInstance(get_record_store("test_record_store.shelf"),
                              shelve_store.ShelveRecordStore)


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
