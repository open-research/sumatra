import urllib2


TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"

def have_internet_connection():
    """
    Not foolproof, but allows checking for an external connection with a short
    timeout, before trying socket.gethostbyname(), which has a very long
    timeout.
    """
    test_address = 'http://74.125.113.99'  # google.com
    try:
        response = urllib2.urlopen(test_address,timeout=1)
        return True
    except urllib2.URLError as err:
        pass
    return False