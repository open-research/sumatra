"""
Handles storage of simulation records on a remote server using HTTP.
"""

from sumatra.recordstore import RecordStore
from sumatra.records import SimRecord
from sumatra import programs, launch, datastore, versioncontrol, parameters, dependency_finder
import httplib2
from urlparse import urlparse
from datetime import datetime
try:
    import json
except ImportError:
    import simplejson as json

def domain(url):
    return urlparse(url).netloc

def encode_record(record):
    data = {
        "group": record.group,
        "reason": record.reason,
        "duration": record.duration,
        "executable": {
            "path": record.executable.path,
            "version": record.executable.version,
            "name": record.executable.name,
         },
        "repository": {
            "url": record.repository.url,
            "type": record.repository.__class__.__name__,
        },
        "main_file": record.main_file,
        "version": record.version,
        "parameters": {
            "content": str(record.parameters),
            "type": record.parameters.__class__.__name__,
        },
        "launch_mode": {
            "type": record.launch_mode.__class__.__name__, 
            "parameters": str(record.launch_mode.get_state()),
        },
        "datastore": {
            "type": record.datastore.__class__.__name__,
            "parameters": str(record.datastore.get_state()),
        },
        "outcome": record.outcome or "",
        "data_key": str(record.data_key),
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "tags": list(record.tags), # not sure if tags should be PUT, perhaps have separate URL for this?
        "diff": record.diff,
        "user": record.user,
        "dependencies": [{
            "path": d.path,
            "version": d.version,
            "name": d.name,
            #"language": d.language,
            "module": d.module,
            "diff": d.diff,
            } for d in record.dependencies],
        "platforms": [{
            "system_name": p.system_name, 
            "ip_addr": p.ip_addr, 
            "architecture_bits": p.architecture_bits, 
            "machine": p.machine, 
            "architecture_linkage": p.architecture_linkage, 
            "version": p.version, 
            "release": p.release, 
            "network_name": p.network_name, 
            "processor": p.processor
            } for p in record.platforms],
        }
    return json.dumps(data)

def keys2str(D):
    E = {}
    for k,v in D.items():
        E[str(k)] = v
    return E

def decode_group_list(content):
    return json.loads(content)

def decode_record_list(content):
    return json.loads(content)

def decode_record(content):
    data = json.loads(content)
    edata = data["executable"]
    cls = programs.registered_program_names.get(edata["name"], programs.Executable)
    executable = cls(edata["path"], edata["version"])
    executable.name = edata["name"]
    rdata = data["repository"]
    repos_cls = None
    for m in versioncontrol.vcs_list:
        if hasattr(m, rdata["type"]):
            repos_cls = getattr(m, rdata["type"])
            break
    if repos_cls is None:  
        repos_cls = versioncontrol.base.Repository
    repository = repos_cls(rdata["url"])
    pdata = data["parameters"]
    if pdata["type"] == "dict":
        parameter_set = eval(pdata["content"])
        assert isinstance(parameter_set, dict)
    else:
        parameter_set = getattr(parameters, pdata["type"])(pdata["content"])
    ldata = data["launch_mode"]
    lm_parameters = eval(ldata["parameters"])
    launch_mode = getattr(launch, ldata["type"])(**lm_parameters)
    ddata = data["datastore"]
    ds_parameters = eval(ddata["parameters"])
    data_store = getattr(datastore, ddata["type"])(**ds_parameters)
    record = SimRecord(executable, repository, data["main_file"],
                       data["version"], parameter_set, launch_mode, data_store,
                       data["group"], data["reason"], data["diff"],
                       data["user"])
    record.tags = set(data["tags"])
    record.timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
    record.data_key = data["data_key"]
    record.duration = data["duration"]
    record.outcome = data["outcome"]
    record.platforms = [launch.PlatformInformation(**keys2str(pldata)) for pldata in data["platforms"]]
    record.dependencies = []
    for depdata in data["dependencies"]:
        dep = getattr(dependency_finder, depdata["module"]).Dependency(depdata["name"], depdata["path"], depdata["version"])
        dep.diff = depdata["diff"]
        record.dependencies.append(dep)
    return record


class  HttpRecordStore(RecordStore):
    
    def __init__(self, server_url, username, password):
        self.server_url = server_url
        if self.server_url[-1] != "/":
            self.server_url += "/"
        self.client = httplib2.Http('.cache')
        self.client.add_credentials(username, password, domain(server_url))
        
    def __str__(self):
        return "Interface to remote record store at %s using HTTP" % self.server_url
        
    #def __getstate__(self):
    #    return self.server_url
    
    #def __setstate__(self, state):
    #    self.__init__(state)

    def _build_url(self, project_name, record):
        return "%s%s/%s/%s" % (self.server_url, project_name, record.group, record.timestamp.strftime("%Y%m%d-%H%M%S"))

    def save(self, project_name, record):
        url = self._build_url(project_name, record)
        headers = {'Content-Type': 'application/json'}
        data = encode_record(record)
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        if response.status not in (200, 201):
            raise Exception("%d\n%s" % (response.status, content))
    
    def _get_record(self, url):
        response, content = self.client.request(url)
        if response.status != 200:
            if response.status == 404:
                raise KeyError("No record was found at %s" % url)                
            else:
                raise Exception("%d\n%s" % (response.status, content))
        return decode_record(content)
    
    def get(self, project_name, label):
        url = "%s%s/%s" % (self.server_url, project_name, label.replace("_", "/"))
        return self._get_record(url)
    
    def list(self, project_name, groups):
        project_url = "%s%s/" % (self.server_url, project_name)
        if groups:
            group_urls = ["%s%s/" % (project_url, group) for group in groups]
        else:
            response, content = self.client.request(project_url)
            assert response.status == 200
            group_urls = decode_group_list(content)["groups"]
        records = []
        for group_url in group_urls:
            response, content = self.client.request(group_url)
            print "<DEBUG>", content, "</DEBUG>"
            record_urls = decode_record_list(content)["records"]
            for record_url in record_urls:
                records.append(self._get_record(record_url))
        return records
    
    def list_for_tags(self, project_name, tags):
        raise NotImplementedError
    
    def delete(self, project_name, label):
        url = "%s%s/%s" % (self.server_url, project_name, label.replace("_", "/"))
        response, deleted_content = self.client.request(url, 'DELETE')
        if response.status != 204:
            raise Exception("%d\n%s" % (response.status, deleted_content))
        
    def delete_group(self, project_name, group_label):
        url = "%s%s/%s/" % (self.server_url, project_name, group_label)
        response, n_records = self.client.request(url, 'DELETE')
        if response.status != 200:
            raise Exception("%d\n%s" % (response.status, n_records))
        return int(n_records)
        
    def delete_by_tag(self, project_name, tag):
        url = "%s%s/tag/%s/" % (self.server_url, project_name, tag)
        response, n_records = self.client.request(url, 'DELETE')
        if response.status != 200:
            raise Exception("%d\n%s" % (response.status, n_records))
        return int(n_records)
    
