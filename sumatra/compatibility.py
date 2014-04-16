"""
Tricks to support Python 2 and Python 3 with the same code base.

"""

try:
    basestring  # Python 2
    string_type = basestring
except NameError:
    string_type = str  # Python 3

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from urllib2 import urlopen, URLError
    from urllib import urlretrieve
    from urlparse import urlparse
except ImportError:
    from urllib.request import urlopen, urlretrieve
    from urllib.error import URLError
    from urllib.parse import urlparse
