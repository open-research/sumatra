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
        self.root_dir = os.path.abspath('kusehgcfscuzhfqizuchgsireugvcsi')
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
        self.ds.archive('test', self.test_files)
        self.assert_(os.path.exists(os.path.join(self.root_dir, 'test.tar.gz')))
        
    def test__archive__should_delete_original_files_if_requested(self):
        assert os.path.exists(os.path.join(self.root_dir, 'test_file1'))
        self.ds.archive('test', self.test_files, delete_originals=True)
        self.assert_(not os.path.exists(os.path.join(self.root_dir, 'test_file1')))
        
    def test__list_files__should_return_a_list_of_found_files(self):
        datafile_list = self.ds.list_files(key=self.test_files)
        self.assertEqual(len(datafile_list), len(self.test_files))
        self.assert_(isinstance(datafile_list[0], DataFile))
        
    def test__get_content__should_return_short_file_content(self):
        content = self.ds.get_content(self.test_files, 'test_file1')
        self.assertEqual(content, self.test_data)
        
    def test__get_content__should_truncate_long_files(self):
        content = self.ds.get_content(self.test_files, 'test_file1', max_length=10)
        self.assertEqual(content, self.test_data[:10])
    
    def test__delete__should_remove_files(self):
        assert os.path.exists(os.path.join(self.root_dir, 'test_file1'))
        self.assertEqual(len(self.ds.list_files(key=self.test_files)), len(self.test_files))
        self.ds.delete(key=self.test_files)
        self.assertEqual(len(self.ds.list_files(key=[])), 0)
        self.assert_(not os.path.exists(os.path.join(self.root_dir, 'test_file1')))


class MockDataStore(object):
        root = os.getcwd()

        
class TestDataFile(unittest.TestCase):   
    
    def setUp(self):
        self.test_file = 'test_file1'
        self.test_data = 'licgsnireugcsenrigucsic\ncrgqgjch,kgch'
        with open(self.test_file, 'w') as f:
            f.write(self.test_data)
        self.data_file = DataFile(self.test_file, MockDataStore())
    
    def tearDown(self):
        os.remove(self.test_file)
    
    def test_init(self):
        pass
    
    def test_str__should_return_path(self):
        self.assertEqual(str(self.data_file), self.data_file.path)
    
    def test_content(self):
        self.assertEqual(self.data_file.content, self.test_data)
        
    def test_sorted_content(self):
        self.assertEqual(self.data_file.sorted_content,
                         'crgqgjch,kgch\nlicgsnireugcsenrigucsic')
        os.remove("%s,sorted" % self.test_file)

    def test_eq(self):
        same_data_file = DataFile(self.test_file, MockDataStore())
        self.assertEqual(self.data_file, same_data_file)
        with open("test_file2", 'w') as f:
            f.write(self.data_file.sorted_content)
        sorted_data_file = DataFile("test_file2", MockDataStore())
        self.assertEqual(self.data_file, sorted_data_file)
        os.remove("test_file2")
        os.remove("test_file2,sorted")
        
    def test_ne(self):
        with open("test_file3", "w") as f:
            f.write("ucyfgnauygfcangf\niauff\ngiurg\n")
        other_data_file = DataFile("test_file3", MockDataStore())
        self.assertNotEqual(self.data_file, other_data_file)
        os.remove("test_file3")
        
class TestModuleFunctions(unittest.TestCase):
    
    def test__get_data_store__should_return_DataStore_object(self):
        root_dir = 'kuqeyfgneuqygvn'
        ds = FileSystemDataStore(root_dir)
        self.assert_(isinstance(get_data_store('FileSystemDataStore', {'root': root_dir}), DataStore))
        
    def test__get_data_store__should_raise_NameError_if_wrong_type(self):
        self.assertRaises(NameError, get_data_store, 'FooDataStore', {})
        
    def test__get_data_store__should_raise_Exception_if_wrong_parameters(self):
        self.assertRaises(TypeError, get_data_store, 'FileSystemDataStore', {'foo': 'kcjghnqlecg'})
        self.assertRaises(TypeError, get_data_store, 'FileSystemDataStore', {'root': 42})
        
if __name__ == '__main__':
    unittest.main()
