"""
Unit tests for the sumatra.web module
"""

import unittest
import os

import sumatra.web
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core import management
from django.core.urlresolvers import reverse

from sumatra.recordstore.django_store import DjangoRecordStore
store = DjangoRecordStore(db_file="test_web.db")

settings.ROOT_URLCONF = 'sumatra.web.urls'
settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['sumatra.web']
management.setup_environ(settings)

from django.test.client import Client
from django.test.utils import setup_test_environment
from test_recordstore import MockRecord
import sumatra.projects

class MockProject(object):
    name = "TestProject"

def add_some_records():
    r1 = MockRecord("record1")
    r2 = MockRecord("record2")
    r3 = MockRecord("record3")
    for r in r1, r2, r3:
        #print "saving record %s" % r.label
        store.save(MockProject.name, r)

class MockDataStore(object):
    def get_content(self, key, path, max_length=100):
        if path == "non_existent_file.txt":
            raise IOError()
        else:
            return ""


sumatra.projects.load_project = lambda: MockProject()

setup_test_environment()

from pprint import pprint


class TestWebInterface(unittest.TestCase):
    
    def test_root(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project_name"],
                         MockProject.name)

    def test__nonexistent_record_should_return_404(self):
        c = Client()
        self.assertRaises(ObjectDoesNotExist,
                          c.get, '/record0/')
 
    def test__record_detail(self):
        add_some_records()
        c = Client()
        response = c.get("/record1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["record"].label, "record1")

    def test__show_file_csv(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.csv")
        assert 'show_csv.html' in [t.name for t in response.template]
        
    def test__show_file_txt(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.txt")
        assert 'show_file.html' in [t.name for t in response.template]

    def test__show_file_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.png")
        assert 'show_image.html' in [t.name for t in response.template]

    def test__show_file_other(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.doc")
        assert 'show_file.html' in [t.name for t in response.template]
        assert "Can't display" in response.context["content"] 

    def test__show_nonexistent_file(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=non_existent_file.txt")
        assert 'show_file.html' in [t.name for t in response.template]
        assert "File not found" in response.context["content"] 

    def test__show_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/image?path=test_file.jpg")
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test__show_diff(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/diff/")
        assert 'show_diff.html' in [t.name for t in response.template]


if __name__ == '__main__':
    unittest.main()