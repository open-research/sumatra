"""
Unit tests for the sumatra.commands module
"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
import hashlib
import shutil
from sumatra import commands, launch, datastore

originals = [] # use for storing originals of mocked objects

class MockDataStore(object):
    def __init__(self, root):
        self.root = root
    def generate_keys(self, *paths):
        return [datastore.DataKey(path, datastore.IGNORE_DIGEST) for path in paths]
    def contains_path(self, path):
        return os.path.exists(path)


class MockExecutable(object):
    def __init__(self, path=None, script_file=None):
        self.path = path
        self.script_file = script_file
    def __eq__(self, other):
        return type(self) == type(other) and self.path == other.path and self.script_file == other.script_file


def mock_get_executable(path=None, script_file=None):
    if path:
        return MockExecutable(path)
    elif script_file:
        if script_file == "file_with_registered_extension":
            return MockExecutable(script_file=script_file)
        else:
            # or return None? advantage of Exception is that calling code has to deal with inability to find executable
            raise Exception("Extension not recognized.")
    else:
        raise Exception('Either path or script_file must be specified')


class MockRecordStore(object):
    def __init__(self, path):
        self.path = path
    def sync(self, other, project):
        return []
    def sync_all(self, other):
        return []


class MockRepository(object):
    def __init__(self, url):
        self.url = url
        self._checkout_called = False
    def checkout(self):
        self._checkout_called = True


class MockRecord(object):
    parameters = {'foo': 23}
    repository = MockRepository("http://hg.example.com")
    input_data = []
    script_arguments = ""
    executable = MockExecutable()
    main_file = "main.py"
    version = "42"
    launch_mode = "dummy"
    def __init__(self, label):
        self.label = label


class MockWorkingCopy(object):
    repository = MockRepository("http://mock_repository")
    

class MockProject(object):
    name = None
    instances = []
    default_repository = "some repository"
    default_main_file = "walk_silly.py"
    default_executable = MockExecutable(path="a.out")
    on_changed = "sound the alarm"
    data_label = "pluck from the ether"
    record_store = MockRecordStore("default")
    saved = False
    info_called = False
    exported = False
    comments = {}
    tags = {}
    removed_tags = {}
    def __init__(self, **kwargs):
        self.data_store = MockDataStore("/path/to/root")
        self.input_datastore = MockDataStore("/path/to/root")
        self.__class__.instances.append(self)
        for k,v in kwargs.items():
            self.__dict__[k] = v
        self._records_deleted = []
    def save(self): self.saved = True
    def info(self): self.info_called = True
    def launch(self, parameters, input_data, script_args, **kwargs):
        self.launch_args = kwargs
        self.launch_args.update(parameters=parameters,
                                input_data=input_data,
                                script_args=script_args)
    def format_records(self, tags, mode, format):
        self.format_args = {"tags": tags, "mode": mode, "format": format}
    def delete_record(self, label, delete_data=False):
        if "nota" in label:
            raise KeyError # or just emit a warning?
        else:
            self._records_deleted.append(label)
    def delete_by_tag(self, tag, delete_data=False):
        self._records_deleted.append("records_tagged_with_%s" % tag)
    def export(self): self.exported = True
    def most_recent(self):
        return MockRecord("most_recent")
    def add_comment(self, label, comment):
        self.comments[label] = comment
    def add_tag(self, label, tag):
        self.tags[label] = tag
    def remove_tag(self, label, tag):
        self.removed_tags[label] = tag
    def compare(self, label1, label2):
        return False
    def show_diff(self, label1, label2, **kwargs):
        return "diff"


def no_project():
    raise Exception("There is no Sumatra project here")

def mock_mkdir(path, mode=0777):
    print "Pretending to create directory %s" % path

def mock_build_parameters(filename):
    if filename != "this.is.not.a.parameter.file":
        ps = type("MockParameterSet", (dict,),
                  {"parameter_file": filename,
                   "pretty": lambda self, expand_urls: str(self)})
        return ps(this="mock")
    else:
        raise SyntaxError


def store_original(module, name):
    global originals
    originals.append((module, name, getattr(module, name)))

def setup():
    store_original(os, "mkdir")
    os.mkdir = mock_mkdir
    for name in ("build_parameters", "get_executable", "get_repository", "get_working_copy", "FileSystemDataStore", "get_record_store"):
        store_original(commands, name)
    commands.build_parameters = mock_build_parameters
    commands.get_executable = mock_get_executable
    commands.get_repository = MockRepository
    commands.get_working_copy = MockWorkingCopy
    commands.get_record_store = MockRecordStore
    commands.FileSystemDataStore = MockDataStore

def teardown():
    for item in originals:
        setattr(*item)


class InitCommandTests(unittest.TestCase):

    def test_with_no_args__should_raise_Exception(self):
        commands.load_project = no_project
        self.assertRaises(SystemExit, commands.init, [])

    def test_with_single_args__should_create_Project(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject"])
        self.assertEqual(MockProject.instances[-1].name, "NewProject")

    def test_with_existing_project_should_return_error(self):
        commands.load_project = lambda: True
        self.assertRaises(SystemExit, commands.init, ["NotSoNewProject"])

    def test_with_repository_option_should_perform_checkout(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "--repository", "/path/to/repos"])
        self.assertEqual(MockProject.instances[-1].default_repository.url, "/path/to/repos")
        self.assert_(MockProject.instances[-1].default_repository._checkout_called, "/path/to/repos")

    def test_set_executable_no_options(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-e", "fooble"])
        prj = MockProject.instances[-1]
        assert prj.saved
        self.assertEqual(prj.default_executable.path, "fooble")

    def test_set_main_no_executable_unregistered_extension_should_set_executable_to_None(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-m", "main.foo"])
        prj = MockProject.instances[-1]
        self.assertEqual(prj.default_main_file, "main.foo")
        self.assertEqual(prj.default_executable, None)

    def test_set_main_no_executable_registered_extension_should_set_executable(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-m", "file_with_registered_extension"])
        prj = MockProject.instances[-1]
        self.assertEqual(prj.default_main_file, "file_with_registered_extension")
        self.assertEqual(prj.default_executable.script_file, "file_with_registered_extension")

    def test_set_executable_and_main(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-m", "main.foo", "-e", "fooble"])
        prj = MockProject.instances[-1]
        self.assertEqual(prj.default_main_file, "main.foo")
        self.assertEqual(prj.default_executable.path, "fooble")

    def test_set_incompatible_executable_and_main(self):
        # not really sure what should happen here. Raise exception or just warning?
        # for now compatibility is not checked
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-m", "main.sli", "-e", "python"])
        prj = MockProject.instances[-1]
        self.assertEqual(prj.default_main_file, "main.sli")
        self.assertEqual(prj.default_executable.path, "python")

    def test_archive_option_set_to_true(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "--archive", "true"])
        prj = MockProject.instances[-1]
        self.assertIsInstance(prj.data_store, datastore.ArchivingFileSystemDataStore)
        self.assertEqual(prj.data_store.archive_store, os.path.abspath(".smt/archive"))

    def test_archive_option_set_to_path(self):
        some_path = "./test_commands_archive_option"
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "--archive", some_path])
        prj = MockProject.instances[-1]
        self.assertIsInstance(prj.data_store, datastore.ArchivingFileSystemDataStore)
        self.assertEqual(prj.data_store.archive_store, os.path.abspath(some_path))
        if os.path.exists(some_path):
            os.rmdir(some_path)

    def test_store_option_should_get_record_store(self):
        commands.load_project = no_project
        commands.Project = MockProject
        commands.init(["NewProject", "-s", "/path/to/store",])
        prj = MockProject.instances[-1]
        self.assertEqual(prj.record_store.path, "/path/to/store")


class ConfigureCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        commands.configure([])
        assert self.prj.saved
        self.assertEqual(self.prj.default_repository, "some repository")
        self.assertEqual(self.prj.default_main_file, "walk_silly.py")
        self.assertEqual(self.prj.default_executable.path, "a.out")
        self.assertEqual(self.prj.on_changed, "sound the alarm")
        self.assertEqual(self.prj.data_label, "pluck from the ether")
        self.assertEqual(self.prj.data_store.root, "/path/to/root")

    def test_with_an_arg(self):
        self.assertRaises(SystemExit, commands.configure, ["foo"])

    def test_set_executable_no_options(self):
        commands.configure(["-e", "python"])
        assert self.prj.saved
        self.assertEqual(self.prj.default_executable.path, "python")

    def test_set_default_script(self):
        commands.configure(["-m", "norwegian.py"])
        assert self.prj.saved
        self.assertEqual(self.prj.default_main_file, "norwegian.py")

    def test_set_default_script_multiple(self):
        commands.configure(["-m", "norwegian.sli mauve.sli"])
        assert self.prj.saved
        self.assertEqual(self.prj.default_main_file, "norwegian.sli mauve.sli")

    def test_set_datastores(self):
        commands.configure(["--datapath", "/path/to/data",
                            "--input", "/path/to/input/data"])
        self.assertEqual(self.prj.data_store.root, "/path/to/data")
        self.assertEqual(self.prj.input_datastore.root, "/path/to/input/data")

    def test_set_on_changed_with_valid_value(self):
        for value in "error", "store-diff":
            commands.configure(["-c", value])
            self.assertEqual(self.prj.on_changed, value)

    def test_set_on_changed_with_invalid_value(self):
        self.assertRaises(SystemExit,
                          commands.configure,
                          ["-c", "runforthehills"])

    def test_set_add_label_with_valid_value(self):
        for value in "cmdline", "parameters":
            commands.configure(["-l", value])
            self.assertEqual(self.prj.data_label, value)

    def test_set_add_label_with_invalid_value(self):
        self.assertRaises(SystemExit,
                          commands.configure,
                          ["-l", "andaprettybow"])

    def test_with_repository_option_should_perform_checkout(self):
        commands.configure(["--repository", "/path/to/another/repos"])
        self.assertEqual(self.prj.default_repository.url, "/path/to/another/repos")
        self.assert_(self.prj.default_repository._checkout_called, "/path/to/repos")

    def test_archive_option_set_to_true(self):
        commands.configure(["--archive", "true"])
        self.assertIsInstance(self.prj.data_store, datastore.ArchivingFileSystemDataStore)
        self.assertEqual(self.prj.data_store.archive_store, ".smt/archive")
        self.prj.data_store = MockDataStore("/path/to/root")

    def test_archive_option_set_to_path(self):
        some_path = "./test_commands_archive_option"
        commands.configure(["--archive", some_path])
        self.assertIsInstance(self.prj.data_store, datastore.ArchivingFileSystemDataStore)
        self.assertEqual(self.prj.data_store.archive_store, some_path)
        if os.path.exists(some_path):
            os.rmdir(some_path)
        self.prj.data_store = MockDataStore("/path/to/root")

    def test_archive_option_set_to_false(self):
        commands.configure(["--archive", "true"])
        self.assertIsInstance(self.prj.data_store, datastore.ArchivingFileSystemDataStore)
        commands.configure(["--archive", "false"])
        self.assert_(not hasattr(self.prj.data_store, "archive_store"))
        self.prj.data_store = MockDataStore("/path/to/root")


class InfoCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_calls_project_info(self):
        self.assertFalse(self.prj.info_called)
        commands.info([])
        self.assertTrue(self.prj.info_called)

    def test_with_args(self):
        self.assertRaises(SystemExit,
                          commands.info,
                          ["foo"])


class TestParseArguments(unittest.TestCase):

    def setUp(self):
        self.input_datastore = MockDataStore('/path/to/root')

    def test_with_no_args(self):
        parameter_sets, input_data, script_args = commands.parse_arguments([], self.input_datastore)
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "")

    def test_with_nonfile_arg(self):
        parameter_sets, input_data, script_args = commands.parse_arguments(["foo"], self.input_datastore)
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "foo")

    def test_with_nonfile_args(self):
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "eggs"],
                                                                           self.input_datastore)
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "spam eggs")

    def test_with_single_parameter_file_and_nonfile_arg(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "test.param"], self.input_datastore)
        self.assertEqual(parameter_sets, [{'this': 'mock'}])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "spam <parameters>")
        os.remove("test.param")

    def test_with_single_datafile(self):
        data_content = "23496857243968b24cbc4275dc82470a\n"
        f = open("this.is.not.a.parameter.file", 'w')
        f.write(data_content)
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(
            ["this.is.not.a.parameter.file"], self.input_datastore)
        self.assertEqual(parameter_sets, [])
        self.assertEqual(os.path.basename(input_data[0].path), "this.is.not.a.parameter.file")
        self.assertEqual(script_args, "this.is.not.a.parameter.file")
        os.remove("this.is.not.a.parameter.file")

    def test_with_cmdline_parameters(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["test.param", "a=17", "umlue=43"], self.input_datastore)
        self.assertEqual(parameter_sets, [{'this': 'mock', 'a': 17, 'umlue': 43}])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "<parameters>")
        os.remove("test.param")

    def test_with_cmdline_parameters_but_no_parameter_set(self):
        self.assertRaises(Exception, commands.parse_arguments, ["a=17", "yagri=43"])

    def test_with_everything(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        data_content = "23496857243968b24cbc4275dc82470a\n"
        f = open("this.is.not.a.parameter.file", 'w')
        f.write(data_content)
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "test.param", "eggs", "this.is.not.a.parameter.file", "a=17", "umlue=43", "beans"],
                                                                           self.input_datastore)
        self.assertEqual(parameter_sets, [{'this': 'mock', 'a': 17, 'umlue': 43}])
        self.assertEqual(os.path.basename(input_data[0].path), "this.is.not.a.parameter.file")
        self.assertEqual(script_args, "spam <parameters> eggs this.is.not.a.parameter.file beans")


class RunCommandTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        commands.run([])
        expected = {'executable': 'default',
                    'parameters': {},
                    'main_file': 'default',
                    'label': None,
                    'input_data': [],
                    'reason': '',
                    'version': 'latest',
                    'launch_mode': launch.SerialLaunchMode(),
                    'script_args': ''}
        self.assertEqual(self.prj.launch_args, expected)

    def test_with_single_script_arg(self):
        commands.run(["some_parameter_file"]) # file doesn't exist so is treated as argument
        self.assertEqual(self.prj.launch_args,
                         {'executable': 'default',
                         'parameters': {},
                         'main_file': 'default',
                         'label': None,
                         'input_data': [],
                         'reason': '',
                         'version': 'latest',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': 'some_parameter_file'})

    def test_with_single_input_file(self):
        data_content = "0.0 242\n0.1 2345\n0.2 42451\n"
        f = open("this.is.not.a.parameter.file", 'w')
        f.write(data_content)
        f.close()
        commands.run(["this.is.not.a.parameter.file"]) # file exists but is not a parameter file so is treated as input data
        self.assertEqual(self.prj.launch_args,
                         {'executable': 'default',
                         'parameters': {},
                         'main_file': 'default',
                         'label': None,
                         'input_data': [datastore.DataKey('this.is.not.a.parameter.file', hashlib.sha1(data_content).hexdigest())],
                         'reason': '',
                         'version': 'latest',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': 'this.is.not.a.parameter.file'})
        os.remove("this.is.not.a.parameter.file")

    def test_with_everything(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        data_content = "23496857243968b24cbc4275dc82470a\n"
        f = open("this.is.not.a.parameter.file", 'w')
        f.write(data_content)
        f.close()
        commands.run(["-l", "vikings", "-v", "234", "--reason='test'",
                      "-e", "python", "--main=main.py", "spam", "test.param",
                      "eggs", "this.is.not.a.parameter.file", "a=17",
                      "umlue=43", "beans"])
        self.assertEqual(self.prj.launch_args,
                         {'executable': MockExecutable('python'),
                         'parameters': {'this': 'mock', 'a': 17, 'umlue': 43},
                         'main_file': 'main.py',
                         'label': 'vikings',
                         'input_data': [datastore.DataKey('this.is.not.a.parameter.file', hashlib.sha1(data_content).hexdigest())],
                         'reason': 'test',
                         'version': '234',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': "spam <parameters> eggs this.is.not.a.parameter.file beans"})
        os.remove("this.is.not.a.parameter.file")
        os.remove("test.param")

    def test_with_command_line_params_but_no_parameter_file(self):
        # ought really to have a more specific Exception and to catch it so as to give a helpful error message to user
        self.assertRaises(Exception, commands.run, ["a=17", "umlue=43"])


class ListCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        commands.list([])
        # need some assertion about self.prj.format_args


class DeleteCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.delete, [])

    def test_with_valid_record_labels(self):
        commands.delete(["recordA", "recordB"])
        self.assertEqual(self.prj._records_deleted,
                         ["recordA", "recordB"])

    def test_with_invalid_record_labels(self):
        commands.delete(["recordA", "notarecordB", "recordC"])
        self.assertEqual(self.prj._records_deleted,
                         ["recordA", "recordC"])

    def test_with_valid_tag(self):
        commands.delete(["--tag", "tagA", "tagB"])
        self.assertEqual(self.prj._records_deleted,
                         ["records_tagged_with_tagA",
                          "records_tagged_with_tagB"])


class CommentCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.comment, [])

    def test_single_arg_interpreted_as_comment_on_last_record(self):
        commands.comment(["that was amazing"])
        self.assertEqual(self.prj.comments["most_recent"], "that was amazing")
    
    def test_two_args_interpreted_as_label_and_comment(self):
        commands.comment(["some_label", "that was appalling"])
        self.assertEqual(self.prj.comments["some_label"], "that was appalling")
    
    #def test_invalid_label(self):
    #    self.fail()
    #
    #def test_with_file_option(self):
    #    self.fail()
    #
    #def test_with_nonexistent_file(self):
    #    self.fail()


class TestTagCommand(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.tag, [])

    def test_single_arg_interpreted_as_tag_on_last_record(self):
        commands.tag(["foo"])
        self.assertEqual(self.prj.tags["most_recent"], "foo")
    
    def test_tag_multiple_records(self):
        commands.tag(["foo", "a", "b", "c"])
        self.assertEqual(self.prj.tags["a"], "foo")
        self.assertEqual(self.prj.tags["b"], "foo")
        self.assertEqual(self.prj.tags["c"], "foo")

    def test_remove_tag(self):
        commands.tag(["-r", "foo", "a", "b"])
        self.assertEqual(self.prj.removed_tags["a"], "foo")
        self.assertEqual(self.prj.removed_tags["b"], "foo")


class RepeatCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.repeat, [])

    def test_repeat_last(self):
        commands.repeat(['last'])
        

class DiffCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.diff, [])

    def test_with_one_arg(self):
        self.assertRaises(SystemExit, commands.diff, ["label1"])

    def test_with_two_args(self):
        commands.diff(["label1", "label2"])


class HelpCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.help, [])

    #def test_help_info(self):
    #    commands.help(["info"])

    def test_help_foo(self):
        self.assertRaises(SystemExit, commands.help, ["foo"])

class UpgradeCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    #def test_project_upgraded(self):
    #    self.fail()  # need to mock shutil, open

    def test_with_args(self):
        self.assertRaises(SystemExit, commands.upgrade, ['foo'])


class ExportCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_project_exported(self):
        commands.export([])
        assert self.prj.exported

    def test_with_args(self):
        self.assertRaises(SystemExit, commands.export, ['foo'])


class SyncCommandTests(unittest.TestCase):

    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj

    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.sync, [])

    def test_with_single_path(self):
        commands.sync(["/path/to/store"])
        
    def test_with_two_paths(self):
        commands.sync(["/path/to/store1", "/path/to/store2"])


class ArgumentParsingTests(unittest.TestCase):

    def test_parse_command_line_parameter_arg_must_contain_equals(self):
        self.assertRaises(Exception, commands.parse_command_line_parameter, "foobar")

    def test_parse_command_line_parameter_with_int(self):
        result = commands.parse_command_line_parameter("a=2")
        self.assertEqual(result, {'a': 2})
        assert isinstance(result['a'], int)

    def test_parse_command_line_parameter_with_float(self):
        result = commands.parse_command_line_parameter("b=2.0")
        self.assertEqual(result, {'b': 2.0})
        assert isinstance(result['b'], float)

    def test_parse_command_line_parameter_with_list(self):
        result = commands.parse_command_line_parameter("c=[1,2,3,4,5]")
        self.assertEqual(result, {'c': range(1,6)})

    def test_parse_command_line_parameter_with_tuple(self):
        result = commands.parse_command_line_parameter("d=('a','b','c')")
        self.assertEqual(result, {'d': ('a', 'b', 'c')})

    def test_parse_command_line_parameter_should_accept_equals_in_parameter(self):
        # because the parameter value could be a string containing "="
        value = "save=Data/result.uwsize=48.setsize=1"
        result = commands.parse_command_line_parameter(value)
        self.assertEqual(result, {'save': 'Data/result.uwsize=48.setsize=1'})


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
