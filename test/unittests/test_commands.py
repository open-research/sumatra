"""
Unit tests for the sumatra.commands module
"""
# just a skeleton for now. Lots more tests needed.

import unittest
import os
from sumatra import commands,launch

originals = [] # use for storing originals of mocked objects

class MockDataStore(object):
    def __init__(self, root):
        self.root = root

class MockProject(object):
    instances = []
    data_store = MockDataStore("/path/to/root")
    default_repository = "some repository"
    default_main_file = "walk_silly.py"
    default_executable = "a.out"
    on_changed = "sound the alarm"
    data_label = "pluck from the ether"
    saved = False
    info_called = False
    def __init__(self, **kwargs):
        self.__class__.instances.append(self)
        for k,v in kwargs.items():
            self.__dict__[k] = v
    def save(self): self.saved = True
    def info(self): self.info_called = True
    def launch(self, parameters, input_data, script_args, **kwargs):
        self.launch_args = kwargs
        self.launch_args.update(parameters=parameters,
                                input_data=input_data,
                                script_args=script_args)
    def format_records(self, tags, mode, format):
        self.format_args = {"tags": tags, "mode": mode, "format": format}

class MockExecutable(object):
    def __init__(self, path=None, script_file=None):
        self.path = path
        self.script_file = script_file
    def __eq__(self, other):
        return self.path == other.path and self.script_file == other.script_file

class MockRepository(object):
    def __init__(self, url):
        pass
    
class MockWorkingCopy(object):
    repository = MockRepository("http://mock_repository")

def no_project():
    raise Exception("There is no Sumatra project here")
    
def mock_mkdir(path):
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
    for name in ("build_parameters", "get_executable", "get_repository", "get_working_copy", "FileSystemDataStore"):
        store_original(commands, name)
    commands.build_parameters = mock_build_parameters
    commands.get_executable = MockExecutable
    commands.get_repository = MockRepository 
    commands.get_working_copy = MockWorkingCopy
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
    

class ConfigureCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj 
    
    def test_with_no_args(self):
        commands.configure([])
        assert self.prj.saved
        self.assertEqual(self.prj.default_repository, "some repository")
        self.assertEqual(self.prj.default_main_file, "walk_silly.py")
        self.assertEqual(self.prj.default_executable, "a.out")
        self.assertEqual(self.prj.on_changed, "sound the alarm")
        self.assertEqual(self.prj.data_label, "pluck from the ether")
        self.assertEqual(self.prj.data_store.root, "/path/to/root")

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


class InfoCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
   
    def test_calls_project_info(self):
        self.assertFalse(self.prj.info_called)
        commands.info([])
        self.assertTrue(self.prj.info_called)


class TestParseArguments(unittest.TestCase):
    
    def test_with_no_args(self):
        parameter_sets, input_data, script_args = commands.parse_arguments([])
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "")

    def test_with_nonfile_arg(self):
        parameter_sets, input_data, script_args = commands.parse_arguments(["foo"])
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "foo")
    
    def test_with_nonfile_args(self):
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "eggs"])
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "spam eggs")
        
    def test_with_single_parameter_file_and_nonfile_arg(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "test.param"])
        self.assertEqual(parameter_sets, [{'this': 'mock'}])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "spam <parameters>")
        os.remove("test.param")
    
    def test_with_single_datafile(self):
        f = open("this.is.not.a.parameter.file", 'w')
        f.write("23496857243968b24cbc4275dc82470a\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(
            ["this.is.not.a.parameter.file"])
        self.assertEqual(parameter_sets, [])
        self.assertEqual(input_data, ["this.is.not.a.parameter.file"])
        self.assertEqual(script_args, "this.is.not.a.parameter.file")
        os.remove("this.is.not.a.parameter.file")

    def test_with_cmdline_parameters(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["test.param", "a=17", "umlue=43"])
        self.assertEqual(parameter_sets, [{'this': 'mock', 'a': 17, 'umlue': 43}])
        self.assertEqual(input_data, [])
        self.assertEqual(script_args, "<parameters>")
        os.remove("test.param")

    def test_with_everything(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        f = open("this.is.not.a.parameter.file", 'w')
        f.write("23496857243968b24cbc4275dc82470a\n")
        f.close()
        parameter_sets, input_data, script_args = commands.parse_arguments(["spam", "test.param", "eggs", "this.is.not.a.parameter.file", "a=17", "umlue=43", "beans"])
        self.assertEqual(parameter_sets, [{'this': 'mock', 'a': 17, 'umlue': 43}])
        self.assertEqual(input_data, ["this.is.not.a.parameter.file"])
        self.assertEqual(script_args, "spam <parameters> eggs this.is.not.a.parameter.file beans")


class TestRunCommand(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
        
    def test_with_no_args(self):
        commands.run([])
        self.assertEqual(self.prj.launch_args,
                        {'executable': 'default',
                         'parameters': {},
                         'main_file': 'default',
                         'label': None,
                         'input_data': [],
                         'reason': None,
                         'version': 'latest',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': ''})

    def test_with_single_script_arg(self):
        commands.run(["some_parameter_file"]) # file doesn't exist so is treated as argument
        self.assertEqual(self.prj.launch_args,
                         {'executable': 'default',
                         'parameters': {},
                         'main_file': 'default',
                         'label': None,
                         'input_data': [],
                         'reason': None,
                         'version': 'latest',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': 'some_parameter_file'})
    
    def test_with_single_input_file(self):
        f = open("this.is.not.a.parameter.file", 'w')
        f.write("0.0 242\n0.1 2345\n0.2 42451\n")
        f.close()
        commands.run(["this.is.not.a.parameter.file"]) # file exists but is not a parameter file so is treated as input data
        self.assertEqual(self.prj.launch_args,
                         {'executable': 'default',
                         'parameters': {},
                         'main_file': 'default',
                         'label': None,
                         'input_data': ['this.is.not.a.parameter.file'],
                         'reason': None,
                         'version': 'latest',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': 'this.is.not.a.parameter.file'})
        os.remove("this.is.not.a.parameter.file")

    def test_with_everything(self):
        f = open("test.param", 'w')
        f.write("a = 2\nb = 3\n")
        f.close()
        f = open("this.is.not.a.parameter.file", 'w')
        f.write("23496857243968b24cbc4275dc82470a\n")
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
                         'input_data': ['this.is.not.a.parameter.file'],
                         'reason': 'test',
                         'version': '234',
                         'launch_mode': launch.SerialLaunchMode(),
                         'script_args': "spam <parameters> eggs this.is.not.a.parameter.file beans"})
        os.remove("this.is.not.a.parameter.file")
        os.remove("test.param")


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


class CommentCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
    
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.comment, [])
        
        
class TestTagCommand(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
    
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.tag, [])
    
    
class RepeatCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
    
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.repeat, [])


class DiffCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
    
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.diff, [])
        
    def test_with_one_arg(self):
        self.assertRaises(SystemExit, commands.diff, ["label1"])


class HelpCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
    
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.help, [])


class ArgumentParsingTests(unittest.TestCase):

    def test_parse_command_line_parameter_should_accept_equals_in_parameter(self):
        # because the parameter value could be a string containing "="
        value = "save=Data/result.uwsize=48.setsize=1"
        result = commands.parse_command_line_parameter(value)
        self.assertEqual(result, {'save': 'Data/result.uwsize=48.setsize=1'})


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()

