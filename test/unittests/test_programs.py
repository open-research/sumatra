"""
Unit tests for the sumatra.programs module
"""
from __future__ import unicode_literals
from builtins import str
from builtins import object

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import distutils.spawn
import sys
import os
try:
    from subprocess import check_output
except ImportError:
    check_output = False
from sumatra.programs import Executable, version_in_command_line_output, get_executable, \
                             PythonExecutable, NESTSimulator, RExecutable


class TestVersionRegExp(unittest.TestCase):

    def test_common_cases(self):
        examples = {
            "NEURON -- Release 7.1 (359:7f113b76a94b) 2009-10-26": "7.1",
            "NEST version 1.9.8498, built on Mar  2 2010 09:40:15 for x86_64-unknown-linux-gnu\nCopyright (C) 1995-2008 The NEST Initiative": "1.9.8498",
            "Python 2.6.2": "2.6.2",
            "abcdefg": "unknown",
            "usage: ls [-ABCFGHLPRSTWabcdefghiklmnopqrstuwx1] [file ...]": "unknown",
            "4.2rc3": "4.2rc3",
            "R scripting front-end version 3.1.2 (2014-10-31)": "3.1.2",
            "First version that reads numbers from 0..1": "unknown",
            "Mature Tool 12.10": "12.10",
            "Beta Tool 0.9.0.dev": "0.9.0.dev",
            "Another Tool 0.8.4.Clumsy message.": "0.8.4"
        }
        for input, output in examples.items():
            self.assertEqual(version_in_command_line_output(input), output)


class TestExecutable(unittest.TestCase):

    def test__init__with_a_full_path_should_just_set_it(self):
        prog = Executable("/bin/ls")
        self.assertEqual(prog.path, "/bin/ls")

    @unittest.skipUnless(check_output, "test requires Python 2.7")
    def test__init__with_only_prog_name__should_try_to_find_full_path(self):
        prog = Executable("ls")
        actual_path = check_output("which ls", shell=True).decode('utf-8').strip()
        self.assertEqual(prog.path, actual_path)

    def test__init__should_find_version_if_possible(self):
        #prog = Executable("/bin/ls")
        #self.assertEqual(prog.version, None) # this is true on Darwin, but not on Ubuntu
        prog = Executable(sys.executable)
        python_version = "%d.%d.%d" % tuple(sys.version_info[:3])
        self.assertEqual(prog.version, python_version)

    def test__str(self):
        prog = Executable(sys.executable)
        str(prog)

    def test__eq(self):
        prog1 = Executable(sys.executable)
        prog2 = Executable(sys.executable)
        prog3 = Executable("/bin/ls")
        self.assertEqual(prog1, prog2)
        assert prog1 != prog3

class TestRExecutable(unittest.TestCase):
    pass

class TestNEURONSimulator(unittest.TestCase):
    pass

class TestNESTSimulator(unittest.TestCase):
    pass

class MockParameterSet(object):
    saved = False
    def save(self, filename, add_extension=False):
        self.saved = True


class TestPythonExecutable(unittest.TestCase):

    def test__write_parameters__should_call_save_on_the_parameter_set(self):
        prog = PythonExecutable(None)
        params = MockParameterSet()
        prog.write_parameters(params, "test_parameters")
        self.assert_(params.saved)


class TestModuleFunctions(unittest.TestCase):

    def test__get_executable__with_path_of_registered_executable(self):
        prog = get_executable("/usr/bin/python")
        assert isinstance(prog, PythonExecutable)
        if os.path.exists("/usr/local/bin/nest"):
            prog = get_executable("/usr/local/bin/nest")
            assert isinstance(prog, NESTSimulator)
        rscript_path = distutils.spawn.find_executable('Rscript')
        if rscript_path is not None:
            prog = get_executable(rscript_path)
            assert isinstance(prog, RExecutable)

    def test__get_executable__with_path_of_unregistered_executable(self):
        prog = get_executable("/bin/cat")
        assert isinstance(prog, Executable)
        self.assertEqual(prog.name, "cat")

    def test__get_executable__with_script_file(self):
        prog = get_executable(script_file="test.py")
        assert isinstance(prog, PythonExecutable)
        prog_r = get_executable(script_file="test.r")
        assert isinstance(prog_r, RExecutable)
        prog_R = get_executable(script_file="test.R")
        assert isinstance(prog_R, RExecutable)

    def test__get_executable__with_nonregistered_extension__should_raise_Exception(self):
        self.assertRaises(Exception, get_executable, script_file="test.foo")

    def test__get_executable__requires_at_least_one_arg(self):
        self.assertRaises(Exception, get_executable)


if __name__ == '__main__':
    unittest.main()
