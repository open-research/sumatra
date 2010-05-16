"""
Handles storage of simulation records on a remote server using HTTP.
"""

from sumatra.recordstore import RecordStore
import httplib2
from urlparse import urlparse
try:
    import json
except ImportError:
    import simplejson as json


def domain(url):
    return urlparse(url).netloc

class  HttpRecordStore(RecordStore):
    
    def __init__(self, server_url, username, password):
        self.server_url = server_url
        if self.server_url != "/":
            self.server_url.append("/")
        self.client = httplib2.Http('.cache')
        self.client.add_credentials(username, password, domain(server_url))

#content.decode('utf-8')
        
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
        data = json.dumps(record, cls=RecordEncoder)
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        assert response.status == "200"
        
    def get(self, project, label):
        url = "%s%s/%s" % (self.server_url, project, label.replace("_", "/"))
        response, content = self.client.request(url)
        assert response.status == "200"
        return json.loads(content)
    
    def list(self, project, groups):
        if groups:
            raise NotImplementedError
        else:
            url = "%s%s/" % (self.server_url, project)
        response, content = self.client.request(url)
        assert response.status == "200"
        return X
    
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
    
    
class RecordEncoder(json.JSONEncoder):
    
    def __init__(self):
        json.JSONEncoder.__init__(self, ensure_ascii=False)
    
    def default(self, record):
        return {
            "group": record.group,
            "reason": record.reason,
            "duration": record.duration,
            "executable": json.dumps(record.executable, cls=ExecutableEncoder),
            "repository": json.dumps(record.repository, cls=RepositoryEncoder),
            "main_file": record.main_file,
            "version": record.version,
            "parameters": json.dumps(record.parameters, cls=ParameterSetEncoder),
            "launch_mode": json.dumps(record.launch_mode, cls=LaunchModeEncoder),
            #"datastore": record.datastore, # do we need to include this? The datastore knows its own identity
            "outcome": record.outcome,
            "data_key": record.data_key,
            "timestamp": record.timestamp,
            "tags": record.tags, # not sure if tags should be PUT, perhaps have separate URL for this?
            "diff": record.diff,
            "user": record.user,
            "dependencies": json.dumps(record.dependencies, cls=DependenciesEncoder),
            "platforms": json.dumps(record.platforms, cls=PlatformInformationEncoder),
        }
        #in case of exception, return json.JSONEncoder.default(self, obj)
        
def build_encoder(*attributes):
    class SimpleJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            D = {}
            for attr in attributes:
                D[attr] = getattr(self, attr)
            return D
    return SimpleJSONEncoder

ExecutableEncoder = build_encoder("name", "path", "version")
RepositoryEncoder =  build_encoder("__class__", "url")
# seems like I'm re-expressing information that pickle already knows how to get (or I can get from __getstate__)
# see http://jsonpickle.github.com/

class ParameterSetEncoder(json.JSONEncoder):
    def default(self, obj):
        pass
        as_dict

class LaunchModeEncoder(json.JSONEncoder):
    def default(self, obj):
        pass
        none or n, mpirun, hosts    

DependenciesEncoder = build_encoder("name", "path", "version", "on_change")

class PlatformInformationEncoder(json.JSONEncoder):
    def default(self, obj):
        pass
        kwargs

def object_hook(obj):
    
