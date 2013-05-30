"""
Unit tests for the sumatra.web module
"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os
from pprint import pprint
import mimetypes
try:
    import docutils
    have_docutils = True
except ImportError:
    have_docutils = False
import sumatra.web
from django.core.exceptions import ObjectDoesNotExist
from django.core import management
from django.core.urlresolvers import reverse
from sumatra.recordstore.django_store import DjangoRecordStore, db_config

import test_recordstore
import sumatra.projects


def setup():
    global store, orig_load_project, Client
    import django.conf
    settings = django.conf.settings
    #store = DjangoRecordStore(db_file="test.db")
    test_recordstore.setup()
    store = test_recordstore.django_store1
    #db_config.configure()
    settings.ROOT_URLCONF = 'sumatra.web.urls'
    settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['sumatra.web']
    management.setup_environ(settings)
    import django.test.client
    Client = django.test.client.Client
    import django.test.utils
    django.test.utils.setup_test_environment()

    #recordstore_setup()
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


def assert_used_template(template_name, response):
    if hasattr(response, "template"):  # Django < 1.5
        templates_used = response.template
    else:
        templates_used = response.templates
    assert template_name in [t.name for t in templates_used], "Response: %s\nContext: %s" % (response.content, response.context) 


class TestWebInterface(unittest.TestCase):
    # note: these tests need to be improved. In general, we don't check much
    # beyond "returns a 200 status code".

    @unittest.skipUnless(have_docutils, "docutils not available")
    def test_project_list(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_record_list(self):
        c = Client()
        response = c.get('/%s/' % MockProject.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project_name"],
                         MockProject.name)

    def test__nonexistent_record_should_return_404(self):
        c = Client()
        self.assertRaises(ObjectDoesNotExist,
                          c.get, '/%s/record0/' % MockProject.name)

    def test_record_list_ajax(self):
        c = Client()
        response = c.get("/%s/" % MockProject.name, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_about_project(self):
        c = Client()
        response = c.get('/%s/about/' % MockProject.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.context["form"].fields.keys()), ["description", "name"])

    def test_update_about_project(self):
        c = Client()
        response = c.post('/%s/about/' % MockProject.name, {"name": "TestProject2", "description": "blah, blah"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].cleaned_data,
                        {'name': u'TestProject2', 'description': u'blah, blah'})

    def test_search(self):
        c = Client()
        response = c.post('/%s/search' % MockProject.name, {'foo': 'bar'})
        self.assertEqual(response.status_code, 200)

    def test_search_fulltext(self):
        c = Client()
        response = c.post('/%s/search' % MockProject.name, {'fulltext_inquiry': 'foo'})
        self.assertEqual(response.status_code, 200)

    def test_list_tags(self):
        c = Client()
        response = c.get('/%s/tag/' % MockProject.name)
        self.assertEqual(response.status_code, 200)

    def test_set_tags(self):
        c = Client()
        response = c.post('/%s/settags' % MockProject.name,
                          {'selected_labels': ['record1', 'record-6'],
                           'tags': ['woo', 'hoo']})
        self.assertEqual(response.status_code, 302)  # redirection

    def test_settings(self):
        c = Client()
        response = c.post('/%s/settings' % MockProject.name,
                          {'display_density': "comfortable", 
                           'nb_records_per_page': 50, 
                           'hidden_cols': ["label", "arguments", "version"]})
        self.assertEqual(response.status_code, 200)

    def test_init_settings(self):
        c = Client()
        response = c.post('/%s/settings' % MockProject.name,
                          {'init_settings': True, 
                           'executable': "Python"})
        self.assertEqual(response.status_code, 200)

    def test__record_detail(self):
        c = Client()
        for label in TEST_LABELS:
            response = c.get("/%s/%s/" % (MockProject.name, label))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["record"].label, label)

    def test__record_detail_post_show_args(self):
        c = Client()
        for label in TEST_LABELS[0:1]:
            response = c.post("/%s/%s/" % (MockProject.name, label),
                              {"show_args": "True"})
            self.assertEqual(response.status_code, 200)
            # should get parameter set back

    def test__record_detail_post_show_script(self):
        sumatra.web.views.get_working_copy = lambda path: MockWorkingCopy()
        c = Client()
        for label in TEST_LABELS[0:1]:
            response = c.post("/%s/%s/" % (MockProject.name, label),
                              {"show_script": "True"})
            self.assertEqual(response.status_code, 200)
            # should get script back

    def test__record_detail_post_compare_records(self):
        c = Client()
        for label in TEST_LABELS[0:1]:
            response = c.post("/%s/%s/" % (MockProject.name, label),
                              {"compare_records": "True",
                               "records": TEST_LABELS[3:5]})
            self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(mimetypes.guess_type("myfile.csv")[0] == 'text/csv', 'CSV mimetype not recognized on this system')
    def test__show_file_csv(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/datafile?path=test_file.csv&digest=mock" % MockProject.name)
        assert_used_template('show_csv.html', response) 

    def test__show_file_txt(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/datafile?path=test_file.txt&digest=mock" % MockProject.name)
        assert_used_template('show_file.html', response)

    def test__show_file_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/datafile?path=test_file.png&digest=mock" % MockProject.name)
        assert_used_template('show_image.html', response)

    def test__show_file_other(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/datafile?path=test_file.doc&digest=mock" % MockProject.name)
        assert_used_template('show_file.html', response)
        assert "Can't display" in response.context["content"]

    def test__show_nonexistent_file(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/datafile?path=non_existent_file.txt&digest=mock" % MockProject.name)
        assert_used_template('show_file.html', response)
        assert "File not found" in response.context["content"]

    def test__show_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/image?path=test_file.jpg&digest=mock" % MockProject.name)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test__show_diff(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/diff" % MockProject.name)
        assert_used_template('show_diff.html', response)
        
    def test_download_file(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/%s/record1/download?path=test_file.txt&digest=mock" % MockProject.name)
        self.assertEqual(response.content, "foo")

    def test_run_sim(self):
        sumatra.web.views.run = lambda options_list: None
        c = Client()
        response = c.post('/%s/simulation' % MockProject.name,
                          {'label': "record7", 
                           'reason': "to see if...", 
                           'tag': "foo", 
                           'execut': "python.exe", 
                           'main_file': "main.py", 
                           'args': "1 2"})
        self.assertEqual(response.status_code, 200)


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
