"""
Unit tests for the sumatra.commands module
"""
# just a skeleton for now. Lots more tests needed.

import unittest
import os
from sumatra import commands


class MockProject(object):
    instances = []
    data_store = type("MockDataStore", (object,), {"root": "/path/to/root"})
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
    def launch(self, parameters, **kwargs):
        self.launch_args = kwargs
        self.launch_args.update(parameters=parameters)
    def format_records(self, tags, mode, format):
        self.format_args = {"tags": tags, "mode": mode, "format": format}

    
class MockExecutable(object):
    def __init__(self, path=None, script_file=None):
        self.path = path
        self.script_file = script_file

class MockRepository(object):
    def __init__(self, url):
        pass
    
class MockWorkingCopy(object):
    repository = MockRepository("http://mock_repository")

commands.get_executable = MockExecutable
commands.get_repository = MockRepository 
commands.get_working_copy = MockWorkingCopy

def no_project():
    raise Exception("There is no Sumatra project here")
    
def mock_mkdir(path):
    print "Pretending to create directory %s" % path
os.mkdir = mock_mkdir    
    
def mock_build_parameters(filename, cmdline):
    ps = type("MockParameterSet", (dict,),
              {"parameter_file": filename,
               "cmdline_parameters": cmdline,
               "pretty": lambda self, expand_urls: ""})
    return ps()
commands.build_parameters = mock_build_parameters
    

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


class InfoCommandTests(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
   
    def test_calls_project_info(self):
        self.assertFalse(self.prj.info_called)
        commands.info([])
        self.assertTrue(self.prj.info_called)


class TestRunCommand(unittest.TestCase):
    
    def setUp(self):
        self.prj = MockProject()
        commands.load_project = lambda: self.prj
        
    def test_with_no_args(self):
        self.assertRaises(SystemExit, commands.run, [])

    def test_with_single_args(self):
        commands.run(["some_parameter_file"])
        # need some assertion about self.prj.launch_args


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


if __name__ == '__main__':
    unittest.main()
