"""
The recordstore sub-package provides an abstraction layer around storage of
simulation/analysis records, providing a common interface to different storage
methods (simple serialisation, relational database, etc.)

Sub-packages/modules
--------------------

shelve_store - provides the ShelveRecordStore class
django_store - provides the DjangoRecordStore class (if Django is installed)
http_store   - provides the HttpRecordStore class


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import os
from sumatra.recordstore import serialization
from .shelve_store import ShelveRecordStore
try:
    from .django_store import DjangoRecordStore
    have_django = True
except ImportError:
    have_django = False
try:
    import httplib2
    have_http = True
except ImportError:
    have_http = False

if have_http:
    from .http_store import HttpRecordStore

DefaultRecordStore = have_django and DjangoRecordStore or ShelveRecordStore


def get_record_store(uri):
    """
    Return the :class:`RecordStore` object found at the given URI (which may be
    a URL or filesystem path).
    """
    if uri[:4] == "http":
        if have_http:
            store = HttpRecordStore(uri)
        else:
            raise Exception("Cannot access record store: httplib2 is not installed.")
    elif os.path.exists(uri) or os.path.exists(uri + ".db"):
        try:
            store = ShelveRecordStore(uri)
        except Exception as err:
            if have_django:
                store = DjangoRecordStore(uri)
            else:
                raise err
    elif os.path.splitext(uri)[1] == ".shelf":
        store = ShelveRecordStore(uri)
    else:
        store = DefaultRecordStore(uri)
    return store
