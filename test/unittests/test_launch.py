"""
Unit tests for the sumatra.launch module
"""

import unittest

class TestPlatformInformation(unittest.TestCase):
    pass

class TestSerialLaunchMode(unittest.TestCase):
    
    def test__get_platform_information_should_return_a_list_of_PlatformInformation_objects(self):
        self.fail()
        
    def test__run__should_raise_an_Exception_if_the_executable_does_not_exist(self):
        self.fail()
    
    def test__run__should_raise_an_Exception_if_the_main_file_does_not_exist(self):
        self.fail()
        
    def test__run__should_raise_an_Exception_if_the_parameter_file_does_not_exist(self):
        self.fail()
    
    def test__run__should_accept_None_for_the_parameter_file_does_not_exist(self):
        self.fail()
    
    def test__run__should_return_False_if_the_command_failed(self):
        self.fail()
        
    def test__run__should_return_True_if_the_command_completed_successfully(self):
        self.fail()


class TestDistributedLaunchMode(unittest.TestCase):
    pass



if __name__ == '__main__':
    unittest.main()