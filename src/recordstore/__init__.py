
class RecordStore(object):
    pass

try:
    from django_store import DjangoRecordStore as DefaultRecordStore
except ImportError:
    from shelve_store import ShelveRecordStore as DefaultRecordStore