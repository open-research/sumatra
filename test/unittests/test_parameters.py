"""
Unit tests for the sumatra.parameters module
"""
from __future__ import with_statement
import unittest
import os
from sumatra.parameters import SimpleParameterSet, NTParameterSet, build_parameters

class TestNTParameterSet(unittest.TestCase):
    pass

class TestSimpleParameterSet(unittest.TestCase):
    
    def test__init__should_accept_space_around_equals(self):
        P = SimpleParameterSet("x = 2\ny = 3")
        self.assertEqual(P["x"], 2)
        self.assertEqual(P["y"], 3)
    
    def test__init__should_accept_no_space_around_equals(self):
        P = SimpleParameterSet("x=2")
        self.assertEqual(P["x"], 2)
        
    def test__init__should_accept_hash_as_comment_character(self):
        P = SimpleParameterSet("x = 2 # this is a comment")
        self.assertEqual(P["x"], 2)
        
    def test__init__should_accept_an_empty_initializer(self):
        P = SimpleParameterSet("")
        self.assertEqual(P.values, {})
        
    def test__init__should_accept_a_filename_or_string(self):
        init = "x = 2\ny = 3"
        P1 = SimpleParameterSet(init)
        with open("test_file", "w") as f:
            f.write(init)
        P2 = SimpleParameterSet("test_file")
        self.assertEqual(P1.values, P2.values)
        os.remove("test_file")
        
    def test__init__should_raise_a_TypeError_if_initializer_is_not_a_filename_or_string(self):
        self.assertRaises(TypeError, SimpleParameterSet, [])
        
    def test__getitem__should_give_access_to_parameters(self):
        P = SimpleParameterSet("x = 2\ny = 3")
        self.assertEqual(P["x"], 2)
        self.assertEqual(P["y"], 3)
        
    def test__getitem__should_raise_a_KeyError_for_a_nonexistent_parameter(self):
        P = SimpleParameterSet("x = 2\ny = 3")
        self.assertRaises(KeyError, P.__getitem__, "z")
        
    def test__pretty__should_put_quotes_around_string_parameters(self):
        init = 'y = "hello"'
        P = SimpleParameterSet(init)
        self.assertEqual(P.pretty(), init)
        
    def test__pretty__should_recreate_comments_in_the_initializer(self):
        init = 'x = 2 # this is a comment'
        P = SimpleParameterSet(init)
        self.assertEqual(P.pretty(), init)
        
    def test__pretty__output_should_be_useable_to_create_an_identical_parameterset(self):
        init = "x = 2\ny = 3\nz = 'hello'"
        P1 = SimpleParameterSet(init)
        P2 = SimpleParameterSet(P1.pretty())
        self.assertEqual(P1.values, P2.values)
        
    def test__save__should_backup_an_existing_file_before_overwriting_it(self):
        # not really sure what the desired behaviour is here
        assert not os.path.exists("test_file.orig")
        init = "x = 2\ny = 3"
        with open("test_file", "w") as f:
            f.write(init)
        P = SimpleParameterSet("test_file")
        P.save("test_file")
        self.assert_(os.path.exists("test_file.orig"))
        os.remove("test_file")
        os.remove("test_file.orig")
        
    def test__update__should_only_accept_numbers_or_strings(self):
        # could maybe allow lists of numbers or strings
        P = SimpleParameterSet("x = 2\ny = 3")
        P.update({"z": "hello"})
        self.assertEqual(P["z"], "hello")
        P.update({"tumoltuae": 42})
        self.assertEqual(P["tumoltuae"], 42)
        self.assertRaises(TypeError, P.update, "bar", {})
    

class TestConfigParserParameterSet(unittest.TestCase):
    pass

class TestModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        init = "x = 2\ny = 3"
        with open("test_file", "w") as f:
            f.write(init)
        init2 = "{\n  'x': 2,\n  'y': {'a': 3, 'b': 4}\n}"
        with open("test_file2", "w") as f:
            f.write(init2)
    
    def tearDown(self):
        os.remove("test_file")
        os.remove("test_file2")
            
    def test__build_parameters__should_add_new_command_line_parameters_to_the_file_parameters(self):
        P = build_parameters("test_file", ["z=42", "foo=bar"])
        self.assertEqual(P.values, {"x": 2, "y": 3, "z": 42, "foo": "bar"})        
                
    def test__build_parameters__should_overwrite_file_parameters_if_command_line_parameters_have_the_same_name(self):
        P = build_parameters("test_file", ["x=12", "y=13"])
        self.assertEqual(P.values, {"x": 12, "y": 13})
        
    def test__build_parameters__should_insert_dotted_parameters_in_the_appropriate_place_in_the_hierarchy(self):
        P = build_parameters("test_file2", ["z=100", "y.c=5", "y.a=-2"])
        assert isinstance(P, NTParameterSet), type(P)
        self.assertEqual(P.as_dict(), {
                                        "y": {
                                            "a": -2,
                                            "b": 4,
                                            "c": 5,
                                        },
                                        "x": 2,
                                        "z": 100,
                                      })
        
        
    def test__build_parameters__should_cast_string_representations_of_numbers_within_lists_to_numeric_type(self):
        # unless they are in quotes
        # also applies to tuples
        # what about dicts or sets?
        self.fail()
    


if __name__ == '__main__':
    unittest.main()