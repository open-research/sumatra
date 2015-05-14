"""
Unit tests for the sumatra.projects module
"""

from __future__ import with_statement
import datetime
import shutil
import os, sys
import unittest
import sumatra.projects
from sumatra.projects import Project, load_project


class MockDiffFormatter(object):
    def __init__(self, diff):
        pass
    def format(self, mode):
        return ""
sumatra.projects.get_diff_formatter = lambda: MockDiffFormatter


# Support the singleton pattern (some cases below require
# the same repository for multiple records).
class SingletonType(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance


class MockRepository(object):
    __metaclass__ = SingletonType
    url = "http://svn.example.com"
    vcs_type = 'git'
    use_version_cmd = ''
    upstream = ''

    def __eq__(self, other):
        return self.url == other.url

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getstate__(self):
        return {}

    def get_working_copy(self):
        return MockWorkingCopy()


class MockWorkingCopy(object):
    path = "/path/to/working/copy"
    repository = MockRepository()
    def has_changed(self):
        return False
    def use_latest_version(self):
        pass
    def current_version(self):
        return 999
    def use_version(self, v):
        pass
    def contains(self, path):
        return True
    def get_username(self):
        return "The Knights Who Say Ni"



class MockExecutable(object):
    name = "Python"
    path = sys.executable  # "/usr/local/bin/python"
    version = sys.version
    requires_script = True
    options = ''
    def write_parameters(self, params, filename):
        pass
    def __getstate__(self):
        return {}


class MockLaunchMode(object):
    working_directory = '/foo/bar'
    def get_platform_information(self):
        return []
    def pre_run(self, prog):
        pass
    def run(self, prog, script, params, append_label):
        return True
    def __getstate__(self):
        return {}


class MockSet(object):
    def __iter__(self):
        return iter(['foo'])
    def add(self, x):
        self.added = x
    def remove(self, x):
        self.removed = x


class MockRecord(object):
    def __init__(self, label):
        self.label = label
        self.tags = MockSet()
        self.parameters = {}
        self.repository = MockRepository()
        self.input_data = []
        self.script_arguments = "-q"
        self.executable = MockExecutable()
        self.main_file = "admin.php"
        self.version = "42"
        self.launch_mode = MockLaunchMode()
        self.outcome = ""
        self.timestamp = datetime.datetime(2042, 0o1, 23)
        self.user = 'user'
        self.duration = 2.3
        self.datastore = MockDatastore()
        self.input_datastore = MockDatastore()
        self.platforms = []
        self.dependencies = []
        self.reason = 'Because'
        self.repeats = None
        self.diff = ''
        self.command_line = '/path/to/program main.script'
        self.stdout_stderr = ''
        self.output_data = []
    def difference(r1, r2, igm, igf):
        return ""


class MockDatastore(object):
    def __init__(self):
        self.root = '/tmp/foo/bar'
    def __getstate__(self):
        return {}


class MockRecordStore(object):
    def save(self, project_name, record):
        pass
    def get(self, project_name, label):
        if label != "none_existent":
            return MockRecord(label=label*2)
        else:
            raise Exception()
    def list(self, project_name, tags=None):
        return [self.get(project_name, 'foo_label'),
                self.get(project_name, 'bar_label')]
    def delete(self, project_name, label):
        self.deleted = label
    def delete_by_tag(self, project_name, tag):
        return "".join(reversed(tag))
    def most_recent(self, project):
        return "last"
    def __getstate__(self):
        return {}


class TestProject(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(".smt"):
            shutil.rmtree(".smt")
        if os.path.exists("Data"):
            os.rmdir("Data")
        if os.path.exists("test.py"):
            os.remove("test.py")

    def write_test_script(self, filename):
        with open(filename, "w") as f:
            f.write("a=2\n")
    write_test_script.__test__ = False  # stop nose treating this as a test

    def test__init__with_minimal_arguments(self):
        proj = Project("test_project", record_store=MockRecordStore())

    def test__creating_a_second_project_in_the_same_dir_should_raise_an_exception(self):
        proj1 = Project("test_project1", record_store=MockRecordStore())
        self.assertRaises(Exception,Project, "test_project2")

    def test__info(self):
        proj = Project("test_project", record_store=MockRecordStore())
        proj.info()

    def test_new_record_with_minimal_args_should_set_defaults(self):
        self.write_test_script("test.py")
        proj = Project("test_project",
                       record_store=MockRecordStore(),
                       default_main_file="test.py",
                       default_executable=MockExecutable(),
                       default_launch_mode=MockLaunchMode(),
                       default_repository=MockRepository())
        rec = proj.new_record()
        self.assertEqual(rec.repository, proj.default_repository)
        self.assertEqual(rec.main_file, "test.py")

    def test_new_record_with_uuid_label_generator_should_generate_unique_id(self):
        self.write_test_script("test.py")
        proj = Project("test_project",
                       record_store=MockRecordStore(),
                       default_main_file="test.py",
                       default_executable=MockExecutable(),
                       default_launch_mode=MockLaunchMode(),
                       default_repository=MockRepository(),
                       label_generator='uuid')
        rec1 = proj.new_record()
        rec2 = proj.new_record()
        self.assertNotEqual(rec1.label, rec2.label)

    def test__update_code(self):
        proj = Project("test_project",
                       record_store=MockRecordStore(),
                       default_repository=MockRepository())
        wc = proj.default_repository.get_working_copy()
        proj.update_code(wc, version=9369835)

    def test_launch(self):
        self.write_test_script("test.py")
        proj = Project("test_project",
                       default_executable=MockExecutable(),
                       default_repository=MockRepository(),
                       default_launch_mode=MockLaunchMode(),
                       record_store=MockRecordStore())
        proj.launch(main_file="test.py")

    def test_format_records(self):
        self.write_test_script("test.py")
        proj = Project("test_project",
                       record_store=MockRecordStore(),
                       default_main_file="test.py",
                       default_executable=MockExecutable(),
                       default_launch_mode=MockLaunchMode(),
                       default_repository=MockRepository(),
                       label_generator='uuid')
        rec1 = proj.new_record()
        rec2 = proj.new_record()
        self.assertEqual(proj.format_records('text'), 'foo_labelfoo_label\nbar_labelbar_label')
        self.assertEqual(proj.format_records('html'), '<ul>\n<li>foo_labelfoo_label</li>\n<li>bar_labelbar_label</li>\n</ul>')
        # TODO: Find a good way to check the output of the following formatters
        #       (currently we only check that we can call them without errors).
        proj.format_records('latex', 'long')
        proj.format_records('shell')
        proj.format_records('json')

    def test__get_record__calls_get_on_the_record_store(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        self.assertEqual(proj.get_record("foo").label, "foofoo")

    def test__delete_record__calls_delete_on_the_record_store(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.delete_record("foo")
        self.assertEqual(proj.record_store.deleted, "foo")

    def test__delete_by_tag__calls_delete_by_tag_on_the_record_store(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        self.assertEqual(proj.delete_by_tag("foo"), "oof")

    def test__add_comment__should_set_the_outcome_attribute_of_the_record(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.add_comment("foo", "comment goes here")

    def test__add_tag__should_call_add_on_the_tags_attibute_of_the_record(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.add_tag("foo", "new_tag")

    def test__remove_tag__should_call_remove_on_the_tags_attibute_of_the_record(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.remove_tag("foo", "new_tag")

    def test__show_diff(self):
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.show_diff("foo", "bar")

    def delete_record__should_update_most_recent(self):
        """see ticket:36."""
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.add_record(MockRecord("record1"))
        self.assertEqual(proj._most_recent, "record1")
        proj.add_record(MockRecord("record2"))
        self.assertEqual(proj._most_recent, "record2")
        proj.delete_record("record2")
        self.assertEqual(proj._most_recent, "last")  # should really be "record1", but we are not testing RecordStore here

    def test__backup(self):
        def fake_copytree(source, target):
            pass
        orig_copytree = shutil.copytree
        shutil.copytree = fake_copytree
        proj = Project("test_project",
                       record_store=MockRecordStore())
        backup_dir = proj.backup()
        shutil.copytree = orig_copytree
        assert "backup" in backup_dir

    def test__repeat(self):
        orig_gwc = sumatra.projects.get_working_copy
        sumatra.projects.get_working_copy = MockWorkingCopy
        orig_launch = Project.launch
        Project.launch = lambda self, **kwargs: "new_record"
        proj = Project("test_project",
                       record_store=MockRecordStore())
        proj.add_record(MockRecord("record1"))
        proj.add_record(MockRecord("record2"))
        self.assertEqual(proj.repeat("record1")[0], "new_record")
        sumatra.projects.get_working_copy = orig_gwc
        Project.launch = orig_launch


class TestModuleFunctions(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(".smt"):
            shutil.rmtree(".smt")
        if os.path.exists("Data"):
            os.rmdir("Data")

    def test__load_project__should_return_Project(self):
        proj1 = Project("test_project", record_store=MockRecordStore())
        assert os.path.exists(".smt/project")
        proj2 = load_project()
        self.assertEqual(proj1.name, proj2.name)

    def test__load_project_should_raise_exception_if_no_project_in_current_dir(self):
        self.assertRaises(Exception, load_project)


if __name__ == '__main__':
    unittest.main()
