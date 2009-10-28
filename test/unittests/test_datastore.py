"""
Unit tests for the sumatra.datastore module
"""

import unittest

class TestFileSystemDataStore(unittest.TestCase):
    
    def test__init__should_create_root_if_it_doesnt_exist(self):
        self.fail()
        
    def test__str__should_return_root(self):
        self.fail()
        
    def test__get_state__should_return_dict_containing_root(self):
        self.fail()
        
    def test__find_new_files__should_return_list_of_new_files(self):
        self.fail()
        
    def test__archive__should_create_a_tarball(self):
        self.fail()
        
    def test__archive__should_delete_original_files_if_requested(self):
        self.fail()
        
    def test__list_files__should_return_a_list_of_found_files(self):
        self.fail()
        
    def test__get_content__should_return_short_file_content(self):
        self.fail()
        
    def test__get_content__should_truncate_long_files(self):
        self.fail()
     
        
class TestModuleFunctions(unittest.TestCase):
    
    def test__get_data_store__should_return_DataStore_object(self):
        self.fail()
        
    def test__get_data_store__should_raise_Exception_if_wrong_type(self):
        self.fail()
        
    def test__get_data_store__should_raise_Exception_if_wrong_parameters(self):
        self.fail()
        
if __name__ == '__main__':
    unittest.main()