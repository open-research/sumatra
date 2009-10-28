"""
Unit tests for the sumatra.parameters module
"""

import unittest

class TestNTParameterSet(unittest.TestCase):
    pass

class TestSimpleParameterSet(unittest.TestCase):
    
    def test__init__should_accept_space_around_equals(self):
        self.fail()
    
    def test__init__should_accept_no_space_around_equals(self):
        self.fail()
        
    def test__init__should_accept_hash_as_comment_character(self):
        self.fail()
        
    def test__init__should_accept_an_empty_initializer(self):
        self.fail()
        
    def test__init__should_accept_a_filename_or_string(self):
        self.fail()
        
    def test__init__should_raise_an_Exception_if_initializer_is_not_a_filename_or_string(self):
        self.fail()
        
    def test__getitem__should_give_access_to_parameters(self):
        self.fail()
        
    def test__getitem__should_raise_an_Exception_for_a_nonexistent_parameter(self):
        self.fail()
        
    def test__pretty__should_put_quotes_around_string_parameters(self):
        self.fail()
        
    def test__pretty__should_recreate_the_initializer_including_comments(self):
        self.fail()
        
    def test__save__should_backup_an_existing_file_before_overwriting_it(self):
        # not really sure what the desired behaviour is here
        self.fail()
        
    def test__update__should_work_as_for_dict(self):
        self.fail()
    

class TestConfigParserParameterSet(unittest.TestCase):
    pass

class TestModuleFunctions(unittest.TestCase):
    
    def test__build_parameters__should_add_new_command_line_parameters_to_the_file_parameters(self):
        self.fail()
        
    def test__build_parameters__should_overwrite_file_parameters_if_command_line_parameters_have_the_same_name(self):
        self.fail()
        
    def test__build_parameters__should_insert_dotted_parameters_in_the_appropriate_place_in_the_hierarchy(self):
        self.fail()
        
    def test__build_parameters__should_cast_string_representations_of_numbers_to_numeric_type(self):
        self.fail()
        
    def test__build_parameters__should_cast_string_representations_of_numbers_within_lists_to_numeric_type(self):
        # unless they are in quotes
        # also applies to tuples
        # what about dicts or sets?
        self.fail()
    


if __name__ == '__main__':
    unittest.main()