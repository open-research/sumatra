"""
Tricks to support Python 2 and Python 3 with the same code base.


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from future import standard_library
standard_library.install_aliases()

try:
    str  # Python 2
    string_type = str
except NameError:
    string_type = str  # Python 3

try:
    from io import StringIO
except ImportError:
    from io import StringIO

try:
    from urllib.request import urlopen
    from urllib.error import URLError
    from urllib.request import urlretrieve
    from urllib.parse import urlparse
except ImportError:
    from urllib.request import urlopen, urlretrieve
    from urllib.error import URLError
    from urllib.parse import urlparse
