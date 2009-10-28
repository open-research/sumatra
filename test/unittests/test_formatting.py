"""
Unit tests for the sumatra.formatting module
"""

import unittest

class TestTextFormatter(unittest.TestCase):
    
    def test__init__should_only_accept_a_list_of_records(self):
        self.fail()
    
    def test__format__should_call_the_appropriate_method(self):
        self.fail()
        
    def test__format__should_raise_an_Exception_with_invalid_mode(self):
        self.fail()
    
    def test__short__should_return_a_multi_line_string(self):
        self.fail()
    
    def test__long__should_return_a_fixed_width_string(self):
        self.fail()

    def test__table__should_return_a_constant_width_string(self):
        self.fail()


class TestHTMLFormatter(unittest.TestCase):
    pass
    

class TestModuleFunctions(unittest.TestCase):
    
    def test__get_formatter__should_return_Formatter_object(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()