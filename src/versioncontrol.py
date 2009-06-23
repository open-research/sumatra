import pysvn
import os.path

class Repository(object):
    
    def __init__(self, url):
        self.url = url
        

class WorkingCopy(object):
    pass

class SubversionWorkingCopy(WorkingCopy):
    pass

class MercurialWorkingCopy(WorkingCopy):

    def __init__(self):
        self.repository = MercurialRepository(os.getcwd()) ###### stub
        self.repository.working_copy = self

class SubversionRepository(Repository):
    
    def __init__(self, url):
        Repository.__init__(self, url)
        self._client = pysvn.Client()
        self.working_copy = None
    
    def checkout(self, path='.'):
        try:
            self._client.checkout(self.url, ".")
        except pysvn._pysvn.ClientError: # assume this is an 'object of the same name already exists' error
            repos_contents = self._client.ls(self.url)
            os.mkdir(".smt_backup")
            for entry in repos_contents:
                filename = entry["name"][len(self.url)+1:]
                if os.path.exists(filename):
                    os.rename(filename,os.path.join(".smt_backup", filename))
            self._client.checkout(self.url, ".")
        self.working_copy = SubversionWorkingCopy()

class MercurialRepository(Repository):
    pass
            
def get_working_copy():
    if os.path.exists(os.path.join(os.getcwd(), ".svn")):
        return SubversionWorkingCopy()
    elif os.path.exists(os.path.join(os.getcwd(), ".hg")):
        return MercurialWorkingCopy()
    else:
        return None
            
def get_repository(url):
    if url:
        return SubversionRepository(url) # we should try to figure out what kind of repos is it, and return the correct kind.
    else:
        working_copy = get_working_copy()
        if working_copy:
            return working_copy.repository
        else:
            return None