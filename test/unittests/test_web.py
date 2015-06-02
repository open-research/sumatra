"""
Unit tests for the sumatra.web module
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
try:
    import docutils
    have_docutils = True
except ImportError:
    have_docutils = False
from datetime import datetime
import sumatra.web
from django.core.exceptions import ObjectDoesNotExist

from . import test_recordstore
import sumatra.projects


def setup():
    global store, orig_load_project, Client
    import django.conf
    settings = django.conf.settings
    test_recordstore.setup()
    store = test_recordstore.django_store1
    settings.ROOT_URLCONF = 'sumatra.web.urls'
    settings.STATIC_URL = '/static/'
    settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['sumatra.web']
    import django.test.client
    Client = django.test.client.Client
    import django.test.utils
    django.test.utils.setup_test_environment()

    orig_load_project = sumatra.projects.load_project
    sumatra.projects.load_project = lambda: MockProject()
    add_some_records()


def clean_up():
    for filename in ("test.db", "test2.db"):
        if os.path.exists(filename):
            os.remove(filename)

def teardown():
    test_recordstore.teardown()
    clean_up()
    sumatra.projects.load_project = orig_load_project


class MockProject(object):
    name = "TestProject"
    default_main_file = "main.py"
    def save(self):
        pass


TEST_LABELS = ('record1', 'record:2', 'record.3', 'record 4', 'record/5', 'record-6')

def add_some_records():
    global store
    for label in TEST_LABELS:
        r = test_recordstore.MockRecord(label)
        if label is "record1":
            r.output_data = [MockDataKey("test_file.csv")]
        store.save(MockProject.name, r)

class MockDataStore(object):
    def get_content(self, key, max_length=100):
        if key.path == "non_existent_file.txt":
            raise IOError()
        else:
            return "foo"

class MockWorkingCopy(object):
    def content(self, digest):
        return "elephants"


class MockDataKey(object):
    def __init__(self, path):
        self.path = path
        self.digest = "mock"
        self.creation = datetime(2001, 1, 1, 0, 0 ,1)

    def __repr__(self):
        return "MockDataKey(%s)" % self.path


def assert_used_template(template_name, response):
    if hasattr(response, "template"):  # Django < 1.5
        templates_used = response.template
    else:
        templates_used = response.templates
    assert template_name in [t.name for t in templates_used], "Response: %s\nContext: %s" % (response.content, response.context)


class TestWebInterface(unittest.TestCase):

    def test__pair_datafiles(self):
        from sumatra.web.views import pair_datafiles
        a = [MockDataKey("file_A_20010101.txt"),
             MockDataKey("file_B.jpg"),
             MockDataKey("file_C.json"),
             MockDataKey("file_D.dat")]
        b = [MockDataKey("file_A_20010202.txt"),
             MockDataKey("datafile_Z.png"),
             MockDataKey("file_C.json")]
        result = pair_datafiles(a, b)
        self.assertEqual(result["matches"],
                         [(a[2], b[2]), (a[0], b[0])])
        self.assertEqual(result["unmatched_a"],
                         [a[1], a[3]])
        self.assertEqual(result["unmatched_b"],
                         [b[1]])


class TestFilters(unittest.TestCase):

    def test__human_readable_duration(self):
        from sumatra.web.templatetags import filters
        self.assertEqual(filters.human_readable_duration(((6 * 60 + 32) * 60 + 12)), '6h 32m 12.00s')
        self.assertEqual(filters.human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60 + 5)), '8d 7h 6m 5.00s')
        self.assertEqual(filters.human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60)), '8d 7h 6m')
        self.assertEqual(filters.human_readable_duration((((8 * 24 + 7) * 60) * 60)), '8d 7h')
        self.assertEqual(filters.human_readable_duration((((8 * 24) * 60) * 60)), '8d')
        self.assertEqual(filters.human_readable_duration((((8 * 24) * 60) * 60) + 0.12), '8d 0.12s')


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
