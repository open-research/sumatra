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


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()

from warnings import warn
from urllib.parse import urlparse, urlunparse
try:
    import httplib2
    have_http = True
except ImportError:
    have_http = False
from sumatra.recordstore.base import RecordStore, RecordStoreAccessError
from sumatra.recordstore import serialization
from ..core import conditional_component


API_VERSION = 4


def domain(url):
    return urlparse(url).netloc


def process_url(url):
    """Strip out username and password if included in URL"""
    username = None
    password = None
    if '@' in url:  # allow encoding username and password in URL - deprecated in RFC 3986, but useful on the command-line
        parts = urlparse(url)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        if parts.port:
            hostname += ":%s" % parts.port
        url = urlunparse((parts.scheme, hostname, parts.path,
                          parts.params, parts.query, parts.fragment))
    return url, username, password


@conditional_component(condition=have_http)
class HttpRecordStore(RecordStore):
    """
    Handles storage of simulation/analysis records on a remote server using HTTP.

    The server should support the following URL structure and HTTP methods:

    =========================================    ================
    /                                            GET
    /<project_name>/[?tags=<tag1>,<tag2>,...]    GET
    /<project_name>/tag/<tag>/                   GET, DELETE
    /<project_name>/<record_label>/              GET, PUT, DELETE
    =========================================    ================

    and should both accept and return JSON-encoded data when the Accept header is
    "application/json".

    The required JSON structure can be seen in :mod:`recordstore.serialization`.
    """

    def __init__(self, server_url, username=None, password=None,
                 disable_ssl_certificate_validation=True):
        self.server_url, _username, _password = process_url(server_url)
        username = username or _username
        password = password or _password
        if self.server_url[-1] != "/":
            self.server_url += "/"
        self.client = httplib2.Http(
            '.cache',
            disable_ssl_certificate_validation=disable_ssl_certificate_validation
        )
        if username:
            self.client.add_credentials(username, password, domain(self.server_url))

    def __str__(self):
        return "Interface to remote record store at %s using HTTP" % self.server_url

    def __getstate__(self):
        username = password = None
        if self.client.credentials.credentials:
            username = self.client.credentials.credentials[0][1]
            password = self.client.credentials.credentials[0][2]
        return {
            'server_url': self.server_url,
            'username': username,
            'password': password,
        }

    def __setstate__(self, state):
        self.__init__(state['server_url'], state['username'], state['password'])

    def _get(self, url, media_type):
        headers = {'Accept': 'application/vnd.sumatra.%s-v%d+json, application/json' % (media_type, API_VERSION)}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def list_projects(self):
        response, content = self._get(self.server_url, 'project-list')
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (self.server_url, response.status, content))
        return [entry['id'] for entry in serialization.decode_project_list(content)]

    def _put_project(self, project_name, long_name='', description=''):
        url = "%s%s/" % (self.server_url, project_name)
        data = serialization.encode_project_info(long_name, description)
        headers = {'Content-Type': 'application/vnd.sumatra.project-v%d+json' % API_VERSION}
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        return response, content

    def create_project(self, project_name, long_name='', description=''):
        """Create an empty project in the record store."""
        response, content = self._put_project(project_name, long_name, description)
        if response.status != 201:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def update_project_info(self, project_name, long_name='', description=''):
        """Update a project's long name and description."""
        response, content = self._put_project(project_name, long_name, description)
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def has_project(self, project_name):
        project_url = "%s%s/" % (self.server_url, project_name)
        response, content = self._get(project_url, 'project')
        if response.status == 200:
            return True
        elif response.status in (401, 404):
            return False
        else:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def project_info(self, project_name):
        """Return a project's long name and description."""
        project_url = "%s%s/" % (self.server_url, project_name)
        response, content = self._get(project_url, 'project')
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (project_url, response.status, content))
        data = serialization.decode_project_data(content)
        return dict((k, data[k]) for k in ("name", "description"))

    def save(self, project_name, record):
        if not self.has_project(project_name):
            self.create_project(project_name)
        url = "%s%s/%s/" % (self.server_url, project_name, record.label)
        headers = {'Content-Type': 'application/vnd.sumatra.record-v%d+json' % API_VERSION}
        data = serialization.encode_record(record)
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        if response.status not in (200, 201):
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def _get_record(self, url):
        response, content = self._get(url, 'record')
        if response.status != 200:
            if response.status == 404:
                raise KeyError("No record was found at %s" % url)
            else:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        return serialization.decode_record(content)

    def get(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        return self._get_record(url)

    def list(self, project_name, tags=None):
        project_url = "%s%s/" % (self.server_url, project_name)
        if tags:
            if not isinstance(tags, list):
                tags = [tags]
            project_url += "?tags=%s" % ",".join(tags)
        response, content = self._get(project_url, 'project')
        if response.status != 200:
            raise RecordStoreAccessError("Could not access %s\n%s: %s" % (project_url, response.status, content))
        record_urls = serialization.decode_project_data(content)["records"]
        records = []
        for record_url in record_urls:
            records.append(self._get_record(record_url))
        return records

    def labels(self, project_name):
        return [record.label for record in self.list(project_name)]  # probably inefficient

    def delete(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        response, deleted_content = self.client.request(url, 'DELETE')
        if response.status != 204:
            raise RecordStoreAccessError("%d\n%s" % (response.status, deleted_content))

    def delete_by_tag(self, project_name, tag):
        url = "%s%s/tag/%s/" % (self.server_url, project_name, tag)
        response, n_records = self.client.request(url, 'DELETE')
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, n_records))
        return int(n_records)

    def most_recent(self, project_name):
        url = "%s%s/last/" % (self.server_url, project_name)
        return self._get_record(url).label

    def sync(self, other, project_name):
        if not self.has_project(project_name):
            self.create_project(project_name)
        super(HttpRecordStore, self).sync(other, project_name)

    def clear(self):
        warn("Cannot clear a remote record store directly. Contact the record store administrator")

    @classmethod
    def accepts_uri(cls, uri):
        return uri[:4] == "http"
