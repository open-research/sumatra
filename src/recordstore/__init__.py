"""
The recordstore sub-package provides an abstraction layer around storage of
simulation/analysis records, providing a common interface to different storage
methods (simple serialisation, relational database, etc.)

Sub-packages/modules
--------------------

shelve_store - provides the ShelveRecordStore class
django_store - provides the DjangoRecordStore class (if Django is installed)
http_store   - provides the HttpRecordStore class
"""

import os
from sumatra.recordstore import serialization
from shelve_store import ShelveRecordStore
try:
    from django_store import DjangoRecordStore
    have_django = True
except ImportError:
    have_django = False
from http_store import HttpRecordStore
DefaultRecordStore = have_django and DjangoRecordStore or ShelveRecordStore

def get_record_store(path):
    if path[:4] == "http":
        store = HttpRecordStore(path)
    elif os.path.exists(path):
        try:
            store = ShelveRecordStore(path)
        except Exception, err:
            if have_django:
                store = DjangoRecordStore(path)
            else:
                raise err
    elif os.path.splitext(path)[1] == ".shelf":
        store = ShelveRecordStore(path)
    else:
        store = DefaultRecordStore(path)
    return store
