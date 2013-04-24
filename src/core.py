"""

"""

import socket
import sys
import locale
from .compatibility import urlopen, URLError


TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"

def have_internet_connection():
    """
    Not foolproof, but allows checking for an external connection with a short
    timeout, before trying socket.gethostbyname(), which has a very long
    timeout.
    """
    test_address = 'http://74.125.113.99'  # google.com
    try:
        response = urlopen(test_address,timeout=1)
        return True
    except (URLError, socket.timeout) as err:
        pass
    return False


def get_encoding():
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        encoding = sys.stdout.encoding
    else:
        encoding = locale.getpreferredencoding()
    return encoding