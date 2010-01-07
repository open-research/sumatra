"""
Unit tests for the sumatra.datastore module
"""

from __future__ import with_statement
import unittest
import tempfile
import shutil
import os
import datetime
from sumatra.datastore import DataStore, FileSystemDataStore, DataFile, get_data_store

class TestFileSystemDataStore(unittest.TestCase):
    
    def setUp(self):
        self.root_dir = 'kusehgcfscuzhfqizuchgsireugvcsi'
        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)
        assert not os.path.exists(self.root_dir)
        self.ds = FileSystemDataStore(self.root_dir)
        self.now = datetime.datetime.now()
        os.mkdir(os.path.join(self.root_dir, 'test_dir'))
        self.test_files = set(['test_file1', 'test_file2', 'test_dir/test_file3'])
        self.test_data = 'licgsnireugcsenrigucsic\ncrgqgjch,kgch'
        for filename in self.test_files:
            with open(os.path.join(self.root_dir, filename), 'w') as f:
                f.write(self.test_data)
    
    def tearDown(self):
        shutil.rmtree(self.root_dir)
        del self.ds
    
    def test__init__should_create_root_if_it_doesnt_exist(self):
        self.assert_(os.path.exists(self.root_dir))
        
    def test__str__should_return_root(self):
        self.assertEqual(str(self.ds), self.root_dir)
        
    def test__get_state__should_return_dict_containing_root(self):
        self.assertEqual(self.ds.get_state(), {'root': self.root_dir})
        
    def test__find_new_files__should_return_list_of_new_files(self):
        self.assertEqual(set(self.ds.find_new_files(self.now)),
                         self.test_files)
        
    def test__find_new_files_with_future_timestamp__should_return_empty_list(self):
        tomorrow = self.now + datetime.timedelta(1)
        self.assertEqual(set(self.ds.find_new_files(tomorrow)),
                         set([]))
        
    def test__archive__should_create_a_tarball(self):
        self.ds.archive(self.now, 'test', 'key_is_not_used?')
        self.assert_(os.path.exists(os.path.join(self.root_dir, 'test.tar.gz')))
        
    def test__archive__should_delete_original_files_if_requested(self):
        assert os.path.exists(os.path.join(self.root_dir, 'test_file1'))
        self.ds.archive(self.now, 'test', 'key_is_not_used?', delete_originals=True)
        self.assert_(not os.path.exists(os.path.join(self.root_dir, 'test_file1')))
        
    def test__list_files__should_return_a_list_of_found_files(self):
        datafile_list = self.ds.list_files(key=self.test_files)
        self.assertEqual(len(datafile_list), len(self.test_files))
        self.assert_(isinstance(datafile_list[0], DataFile))
        
    def test__get_content__should_return_short_file_content(self):
        content = self.ds.get_content('key_not_used', 'test_file1')
        self.assertEqual(content, self.test_data)
        
    def test__get_content__should_truncate_long_files(self):
        content = self.ds.get_content('key_not_used', 'test_file1', max_length=10)
        self.assertEqual(content, self.test_data[:10])
     
        
class TestModuleFunctions(unittest.TestCase):
    
    def test__get_data_store__should_return_DataStore_object(self):
        root_dir = 'kuqeyfgneuqygvn'
        ds = FileSystemDataStore(root_dir)
        self.assert_(isinstance(get_data_store('FileSystemDataStore', {'root': root_dir}), DataStore))
        shutil.rmtree(root_dir)
        
    def test__get_data_store__should_raise_NameError_if_wrong_type(self):
        self.assertRaises(NameError, get_data_store, 'FooDataStore', {})
        
    def test__get_data_store__should_raise_Exception_if_wrong_parameters(self):
        self.assertRaises(TypeError, get_data_store, 'FileSystemDataStore', {'foo': 'kcjghnqlecg'})
        self.assertRaises(TypeError, get_data_store, 'FileSystemDataStore', {'root': 42})
        
if __name__ == '__main__':
    unittest.main()