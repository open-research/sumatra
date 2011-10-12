"""
Handles storage of simulation/analysis records on a remote server using HTTP.

The server should support the following URL structure and HTTP methods:

/                                            GET
/<project_name>/[?tags=<tag1>,<tag2>,...]    GET
/<project_name>/tag/<tag>/                   GET, DELETE
/<project_name>/<record_label>/              GET, PUT, DELETE

and should both accept and return JSON-encoded data when the Accept header is
"application/json".

The required JSON structure can be seen in recordstore.serialization.
"""

from sumatra.recordstore.base import RecordStore
from sumatra.recordstore import serialization
import httplib2
from urlparse import urlparse, urlunparse


def domain(url):
    return urlparse(url).netloc


def process_url(url):
    """Strip out username and password if included in URL"""
    username = None; password = None
    if '@' in url: # allow encoding username and password in URL - deprecated in RFC 3986, but useful on the command-line
        parts = urlparse(url)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        if parts.port:
            hostname += ":%s" % parts.port
        url = urlunparse((parts.scheme, hostname, parts.path, parts.params, parts.query, parts.fragment))
    return url, username, password


class HttpRecordStore(RecordStore):
    
    def __init__(self, server_url, username=None, password=None):
        self.server_url, _username, _password = process_url(server_url)
        username = username or _username
        password = password or _password
        if self.server_url[-1] != "/":
            self.server_url += "/"
        self.client = httplib2.Http('.cache')
        if username:
            self.client.add_credentials(username, password, domain(server_url))
        
    def __str__(self):
        return "Interface to remote record store at %s using HTTP" % self.server_url

    def __getstate__(self):
        return {
            'server_url': self.server_url,
            'username': self.client.credentials.credentials[0][1],
            'password': self.client.credentials.credentials[0][2],
        }
    
    def __setstate__(self, state):
        self.__init__(state['server_url'], state['username'], state['password'])

    def list_projects(self):
        response, content = self.client.request(self.server_url)
        if response.status != 200:
            raise Exception("Error in accessing %s\n%s: %s" % (self.server_url, response.status, content))
        return serialization.decode_project_list(content)

    def save(self, project_name, record):
        url = "%s%s/%s/" % (self.server_url, project_name, record.label)
        headers = {'Content-Type': 'application/json'}
        data = serialization.encode_record(record)
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
        return serialization.decode_record(content)
    
    def get(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        return self._get_record(url)
    
    def list(self, project_name, tags=None):
        project_url = "%s%s/" % (self.server_url, project_name)
        if tags:
            if not hasattr(tags, "__iter__"):
                tags=[tags]
            project_url += "?tags=%s" % ",".join(tags)
        response, content = self.client.request(project_url)
        if response.status != 200:
            raise Exception("Error in accessing %s\n%s: %s" % (project_url, response.status, content))
        record_urls = serialization.decode_record_list(content)["records"]
        records = []
        for record_url in record_urls:
            records.append(self._get_record(record_url))
        return records
    
    def labels(self, project_name):
        return [record.label for record in self.list(project_name)] # probably inefficient
    
    def delete(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        response, deleted_content = self.client.request(url, 'DELETE')
        if response.status != 204:
            raise Exception("%d\n%s" % (response.status, deleted_content))
        
    def delete_by_tag(self, project_name, tag):
        url = "%s%s/tag/%s/" % (self.server_url, project_name, tag)
        response, n_records = self.client.request(url, 'DELETE')
        if response.status != 200:
            raise Exception("%d\n%s" % (response.status, n_records))
        return int(n_records)
    
    def most_recent(self, project_name):
        url = "%s%s/last/" % (self.server_url, project_name)
        return self._get_record(url).label
