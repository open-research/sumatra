import os.path

class FileSystemDataStore(object):
    
    def __init__(self, root):
        self.root = root or "./Data"
        if not os.path.exists(self.root):
            os.mkdir(self.root)
