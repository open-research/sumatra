"""
The recordstore sub-package provides an abstraction layer around storage of
simulation records, providing a common interface to different storage methods
(simple serialisation, relational database, etc.)

Sub-packages/modules
--------------------

shelve_store - provides the ShelveRecordStore class
django_store - provides the DjangoRecordStore class (if Django is installed) 
"""

class RecordStore(object):
    pass

try:
    from django_store import DjangoRecordStore as DefaultRecordStore
except ImportError:
    from shelve_store import ShelveRecordStore as DefaultRecordStore