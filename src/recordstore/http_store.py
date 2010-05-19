"""
Handles storage of simulation records on a remote server using HTTP.
"""

from sumatra.recordstore import RecordStore
import httplib2
from urlparse import urlparse
import jsonpickle

def domain(url):
    return urlparse(url).netloc

class  HttpRecordStore(RecordStore):
    
    def __init__(self, server_url, username, password):
        self.server_url = server_url
        if self.server_url != "/":
            self.server_url += "/"
        self.client = httplib2.Http('.cache')
        self.client.add_credentials(username, password, domain(server_url))
        
    def __str__(self):
        return "Interface to remote record store at %s using HTTP" % self.server_url
        
    #def __getstate__(self):
    #    return self.server
    
    #def __setstate__(self, state):
    #    self.__init__(state)

    def _build_url(self, record):
        return "%s%s/%s/%s" % (self.server_url, record.project, record.group, record.timestamp.strftime("%Y%m%d-%H%M%S"))

    def save(self, record):
        url = self._build_url(record)
        headers = {'Content-Type': 'application/json'}
        data = jsonpickle.encode(record) # in future, unpicklable=False should give nicer json, but then we'll have to parse it more by hand
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        assert response.status == "200"
        
    def get(self, project, label):
        url = "%s%s/%s" % (self.server_url, project, label.replace("_", "/"))
        response, content = self.client.request(url)
        assert response.status == "200"
        return jsonpickle.decode(content)
    
    def list(self, project, groups):
        if groups:
            raise NotImplementedError
        else:
            url = "%s%s/" % (self.server_url, project)
        response, content = self.client.request(url)
        assert response.status == "200"
        return jsonpickle.decode(content)
    
    def delete(self, project, label):
        url = "%s%s/%s" % (self.server_url, project, label)
        response, deleted_content = self.client.request(url, 'DELETE')
        assert response.status == "200"
        
    def delete_group(self, project, group_label):
        "%s%s/%s/" % (self.server_url, project, group_label)
        response, deleted_content = self.client.request(url, 'DELETE')
        assert response.status == "200"
        
    def delete_by_tag(self, project, tag):
        raise NotImplementedError
    
