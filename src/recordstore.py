import shelve


class RecordStore(object):
    pass


class ShelveRecordStore(object):
    
    def __init__(self, shelf_name):
        self.shelf = open(shelf_name)
        

class DjangoRecordStore(object):
    pass