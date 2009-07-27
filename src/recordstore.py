import shelve


class RecordStore(object):
    pass


class ShelveRecordStore(object):
    
    def __init__(self, shelf_name):
        self._shelf_name = shelf_name
        self.shelf = shelve.open(shelf_name)
        
    def __del__(self):
        self.shelf.close()
        
    def __str__(self):
        return "shelve"
        
    def __getstate__(self):
        return self._shelf_name
    
    def __setstate__(self, state):
        self.__init__(state)

class DjangoRecordStore(object):
    pass