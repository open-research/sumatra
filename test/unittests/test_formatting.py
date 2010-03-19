"""
Unit tests for the sumatra.formatting module
"""

import unittest
from datetime import datetime
from sumatra.records import SimRecord
from sumatra.formatting import Formatter, TextFormatter, HTMLFormatter, TextDiffFormatter, get_formatter

class MockRecord(SimRecord):
    def __init__(self):
        self.group = ""
        self.reason = ""
        self.outcome = ""
        self.duration = ""
        self.repository = ""
        self.main_file = ""
        self.version = ""
        self.executable = ""
        self.timestamp = datetime.now()
        self.tags = ""

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
    data_differs = True
    data_differences = {}
    main_file_differs = True
    version_differs = True
    diff_differs = True
    parameters_differ = True
    

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
        #self.assertEqual(tf1.format(mode='table'), tf1.table())
        
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

    #def test__table__should_return_a_constant_width_string(self):
    #    self.fail()


class TestHTMLFormatter(unittest.TestCase):
    pass

    
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