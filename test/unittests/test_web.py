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
from datetime import datetime


class MockDataKey(object):

    def __init__(self, path):
        self.path = path
        self.digest = "mock"
        self.creation = datetime(2001, 1, 1, 0, 0, 1)

    def __repr__(self):
        return "MockDataKey(%s)" % self.path


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
    unittest.main()
