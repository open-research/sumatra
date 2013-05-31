"""
Unit tests for the sumatra.formatting module
"""

import unittest
import tempfile
from datetime import datetime
import os
import shutil
from xml.etree import ElementTree

from sumatra.records import Record
from sumatra.formatting import (Formatter, TextFormatter, HTMLFormatter,
                                TextDiffFormatter, get_formatter,
                                ShellFormatter, LaTeXFormatter)
from sumatra.core import run, TIMESTAMP_FORMAT
from sumatra.programs import get_executable


class MockRepository(object):
    vcs_type = "mockvcs"
    use_version_cmd = "mck use-this-version"
    apply_patch_cmd = "mck apply-this-patch"
    def __init__(self, url, upstream=None):
        self.url = url
        self.upstream = upstream
    def __hash__(self):
        return hash(self.url)
    def __eq__(self, other):
        return self.url == other.url
    def __repr__(self):
        return "MockRepository(%s)" % self.url
    

class MockExecutable(object):
    name = "brian"
    version = "99.99"
    def write_parameters(self, param, filebase):
        return "filename"
    def __repr__(self):
        return "MockExecutable()" 


class MockLaunchMode(object):
    working_directory = "/path/to/wd"
    def generate_command(self, ex, main, args):
        return ex.name + " " + main + " " + args
    def __repr__(self):
        return "MockLaunchMode()" 


class MockDataItem(object):
    def __init__(self, path):
        self.path = path
        self.metadata = {'size': 1024}
    def __repr__(self):
        return self.path
    

class MockRecord(Record):
    def __init__(self):
        self.timestamp = datetime.now()
        self.label = self.timestamp.strftime(TIMESTAMP_FORMAT)
        self.reason = "determine how many shekels the gourd is worth"
        self.outcome = "apparently it is worth NaN shekels"
        self.duration = 1.2345
        self.repository = MockRepository("http://cvs.example.com/pfj/")
        self.main_file = "haggle.py"
        self.version = "5.4.3"
        self.executable = MockExecutable()
        self.tags = ["splitters",]
        self.script_arguments = "arg1 arg2"
        self.input_data = [MockDataItem('somefile'),
                           MockDataItem('anotherfile')]
        self.diff = 'iuefciaeufhmc'
        self.parameters = {'a': 2, 'b': 4}
        self.launch_mode = MockLaunchMode()
        self.output_data = []
        self.user = 'King Arthur <boss@camelot.gov>'
        self.repeats = None
        self.platforms = []
        self.dependencies = []
        self.datastore = "datastore"


class MockRecordDifference(object):
    recordA = MockRecord()
    recordB = MockRecord()
    dependencies_differ = True
    executable_differs = True
    dependency_differences = {}
    code_differs = True
    repository_differs = True
    launch_mode_differs = True
    launch_mode_differences = {}
    output_data_differ = True
    output_data_differences = (['foo'], [])
    main_file_differs = True
    version_differs = True
    diff_differs = True
    parameters_differ = True
    input_data_differ = True
    script_arguments_differ = True


class MockProject(object):
    name = "ExampleProject"
    description = "This is an example project."
    path = "/path/to/project"


class TestTextFormatter(unittest.TestCase):

    def setUp(self):
        self.record_list = [ MockRecord(), MockRecord() ]
        self.record_tuple = ( MockRecord(), MockRecord() )

    def test__init__should_accept_an_iterable_containing_records(self):
        tf1 = TextFormatter(self.record_list)
        tf2 = TextFormatter(self.record_tuple)

    def test__format__should_call_the_appropriate_method(self):
        tf1 = TextFormatter(self.record_list)
        self.assertEqual(tf1.format(mode='short'), tf1.short())
        self.assertEqual(tf1.format(mode='long'), tf1.long())
        self.assertEqual(tf1.format(mode='table'), tf1.table())

    def test__format__should_raise_an_Exception_with_invalid_mode(self):
        tf1 = TextFormatter(self.record_list)
        self.assertRaises(AttributeError, tf1.format, "foo")

    def test__short__should_return_a_multi_line_string(self):
        tf1 = TextFormatter(self.record_list)
        txt = tf1.short()
        self.assertEqual(len(txt.split("\n")), len(tf1.records))

    def test__long__should_return_a_fixed_width_string(self):
        tf1 = TextFormatter(self.record_list)
        txt = tf1.long()
        lengths = [len(line) for line in txt.split("\n")]
        self.assert_(max(lengths)  <= 80)

    def test__table__should_return_a_constant_width_string(self):
        tf1 = TextFormatter(self.record_list)
        txt = tf1.table()
        lengths = [len(line) for line in txt.split("\n")[:-1]]
        for l in lengths:
            assert l == lengths[0]


class TestShellFormatter(unittest.TestCase):

    def setUp(self):
        self.record_list = [ MockRecord(), MockRecord() ]

    def test__short(self):
        tf1 = ShellFormatter(self.record_list, project=MockProject())
        txt = tf1.short()
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir,"test.sh"), "w") as fp:
            fp.write(txt)
        returncode, stdout, stderr = run(["sh", "-n", "test.sh"], cwd=tmpdir)  # check syntax
        self.assertEqual(returncode, 0)
        shutil.rmtree(tmpdir)


class TestLaTeXFormatter(unittest.TestCase):

    def setUp(self):
        self.record_list = [ MockRecord(), MockRecord() ]

    def test__long(self):
        tf1 = LaTeXFormatter(self.record_list, project=MockProject())
        txt = tf1.long()
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "test.tex"), "w") as fp:
            fp.write(txt)
        if get_executable("pdflatex").path == "pdflatex":  # pdflatex not found
            raise unittest.SkipTest
        else:
            returncode, stdout, stderr = run(["pdflatex", "test.tex"], cwd=tmpdir)  # check it builds
            output = stdout + stderr
            if returncode != 0:
                if "not found" in output:  # one of the required LaTeX packages is unavailable
                    raise unittest.SkipTest
                else:
                    self.fail(output)
        shutil.rmtree(tmpdir)


class TestHTMLFormatter(unittest.TestCase):

    def setUp(self):
        self.record_list = [ MockRecord(), MockRecord() ]
        self.record_tuple = ( MockRecord(), MockRecord() )

    def test__short__should_return_an_unordered_list(self):
        hf1 = HTMLFormatter(self.record_list)
        doc = ElementTree.fromstring(hf1.short())
        self.assertEqual(doc.tag, 'ul')
        self.assertEqual(len(doc.getchildren()), 2)

    def test__long__should_return_a_definition_list(self):
        hf1 = HTMLFormatter(self.record_list)
        doc = ElementTree.fromstring(hf1.long())
        self.assertEqual(doc.tag, 'dl')
        self.assertEqual(len(doc.findall("dt")), 2)
        self.assertEqual(len(doc.findall("dd")), 2)
        first_record = doc.find("dd")
        self.assertEqual(len(first_record.getchildren()), 1)
        self.assertEqual(first_record.getchildren()[0].tag, "dl")
        # this test is rather limited.

    def test__table__should_return_an_html_table(self):
        hf1 = HTMLFormatter(self.record_list)
        doc = ElementTree.fromstring(hf1.table())
        self.assertEqual(doc.tag, 'table')
        self.assertEqual(len(doc.findall("tr")), 3)


class TestTextDiffFormatter(unittest.TestCase):

    def setUp(self):
        self.df = TextDiffFormatter(MockRecordDifference())

    def test__init(self):
        pass

    def test__short(self):
        txt = self.df.short()

    def test__long(self):
        txt = self.df.long()



class TestModuleFunctions(unittest.TestCase):

    def test__get_formatter__should_return_Formatter_subclass(self):
        for format in 'text', 'html', 'textdiff':
            assert issubclass(get_formatter(format), Formatter)


if __name__ == '__main__':
    unittest.main()
