"""

"""
from __future__ import unicode_literals
from builtins import object

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
import shutil
from io import StringIO
from textwrap import dedent
try:
    from docutils.core import publish_string
    have_docutils = True
except ImportError:
    have_docutils = False
from sumatra.publishing import utils
from sumatra.publishing.latex import includefigure
if have_docutils:
    from sumatra.publishing.sphinxext import sumatra_rst
from sumatra.datastore import DataKey
from .utils import patch

class MockRecordStore(object):

    def __init__(self, store_location):
        if store_location.startswith("http"):
            self.server_url = store_location

    def get(self, project_name, label):
        return MockRecord(label)


class MockDataStore(object):

    def get_data_item(self, key):
        return MockDataItem(key)


class MockDataItem(object):

    def __init__(self, key):
        self.key = key

    def save_copy(self, path):
        return os.path.join(path, self.key.path)


class MockRecord(object):

    def __init__(self, label):
        self.label = label
        key = DataKey("bar.jpg", "0123456789abcdef")
        other_key = DataKey("subdirectory/baz.png", "fedcba9876543210")
        #key.url = "http://example.com/my_data/bar.jpg"
        self.output_data = [key, other_key]
        self.datastore = MockDataStore()


class MockProject(object):
    name = "MyProject"

    def __init__(self, path=None):
        self.path = path
        self.record_store = MockRecordStore("/path/to/store")


def teardown():
    if os.path.exists(".smt"):
        shutil.rmtree(".smt")


class TestUtils(unittest.TestCase):

    def setUp(self):
        utils._cache = {}

    @patch(utils, "load_project", MockProject)
    def test_determine_project_with_project_dir(self):
        prj = utils.determine_project({'project_dir': '/path/to/project'})
        self.assertEqual(prj.path, '/path/to/project')

    @patch(utils, "load_project", MockProject)
    def test_determine_project_with_local_project(self):
        os.mkdir(".smt")
        open(os.path.join(".smt", "project"), "w").close()  # create empty file
        prj = utils.determine_project({})
        self.assertEqual(prj.path, None)
        shutil.rmtree(".smt")

    def test_determine_project_with_no_project(self):
        prj = utils.determine_project({})
        self.assertEqual(prj, None)

    def test_determine_record_store_from_project(self):
        store = utils.determine_record_store(MockProject(), {})
        self.assert_(isinstance(store, MockRecordStore))

    def test_determine_record_store_with_no_options_no_project(self):
        self.assertRaises(Exception, utils.determine_record_store, None, {})

    def test_determine_project_name_from_local_project(self):
        name = utils.determine_project_name(MockProject(), {})
        self.assertEqual(name, "MyProject")

    def test_determine_project_name_no_project(self):
        self.assertRaises(Exception, utils.determine_project_name, None, {})



class TestLaTeX(unittest.TestCase):

    def setUp(self):
        utils._cache = {}

    def test_read_config(self):
        config = dedent("""
            [sumatra]
            label: foo
            project: MyProject
            record_store: /path/to/db
            digest: 0123456789abcdef
            [graphics]
            width: 0.9\textwidth
            """)
        test_file = "test_latex.config"
        with open(test_file, "w") as fp:
            fp.write(config)
        self.assertEqual(includefigure.read_config(test_file),
                         ({"label": "foo",
                           "project": "MyProject",
                           "record_store": "/path/to/db",
                           "digest": "0123456789abcdef"},
                          {"width": "0.9\textwidth"}))
        os.remove(test_file)

    @patch(utils, 'get_record_store', MockRecordStore)
    def test_generate_latex_command(self):
        sumatra_options = {
            "label": "foo",
            "project": "MyProject",
            "record_store": "/path/to/db",
        }
        graphics_options = {
            "width": "\textwidth",
        }
        sys.stdout = StringIO()
        cmd = includefigure.generate_latex_command(sumatra_options, graphics_options)
        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read().strip(),
                         "\includegraphics[width=\textwidth]{smt_images/bar.jpg}")
        sys.stdout = sys.__stdout__

    @patch(utils, 'get_record_store', MockRecordStore)
    def test_generate_latex_command__with_path(self):
        sumatra_options = {
            "label": "foo:subdirectory/baz.png",
            "project": "MyProject",
            "record_store": "/path/to/db",
        }
        graphics_options = {
            "width": "\textwidth",
        }
        sys.stdout = StringIO()
        cmd = includefigure.generate_latex_command(sumatra_options, graphics_options)
        sys.stdout.seek(0)
        self.assertEqual(sys.stdout.read().strip(),
                         "\includegraphics[width=\textwidth]{smt_images/subdirectory/baz.png}")
        sys.stdout = sys.__stdout__

@unittest.skipUnless(have_docutils, "docutils not available")
class TestSphinx(unittest.TestCase):
    """
    [general]
    sumatra_record_store: https://smt.andrewdavison.info/records
    sumatra_project: Destexhe_JCNS_2009
    sumatra_link_icon: icon_info.png
    """

    def setUp(self):
        utils._cache = {}

    def tearDown(self):
        os.remove("docutils.conf")

    @patch(utils, 'get_record_store', MockRecordStore)
    def test_full_build(self):
        source = dedent("""
            .. smtimage:: foo
               :digest: 0123456789abcdef
               :align: center
            """)
        config = dedent("""
            [general]
            sumatra_record_store: /path/to/db
            sumatra_project: MyProject
            sumatra_link_icon: icon_info.png
            """)
        with open("docutils.conf", "w") as fp:
            fp.write(config)
        output = publish_string(source, writer_name='pseudoxml',
                                settings_overrides={'output_encoding': 'unicode'})
        self.assertEqual("\n" + output,
                         dedent("""
                            <document source="<string>">
                                <image align="center" alt="Data file generated by computation foo" digest="0123456789abcdef" uri="smt_images/bar.jpg">
                            """))



    @patch(utils, 'get_record_store', MockRecordStore)
    def test_full_build_http_store(self):
        source = dedent("""
            .. smtimage:: foo
               :digest: 0123456789abcdef
               :align: center
            """)
        config = dedent("""
            [general]
            sumatra_record_store: http://smt.example.com/
            sumatra_project: MyProject
            sumatra_link_icon: icon_info.png
            """)
        with open("docutils.conf", "w") as fp:
            fp.write(config)
        output = publish_string(source, writer_name='pseudoxml',
                                settings_overrides={'output_encoding': 'unicode'})
        self.assertEqual("\n" + output,
                         dedent("""
                            <document source="<string>">
                                <reference refuri="http://smt.example.com/MyProject/foo/">
                                    <image align="center" alt="Data file generated by computation foo" digest="0123456789abcdef" uri="smt_images/bar.jpg">
                            """))
