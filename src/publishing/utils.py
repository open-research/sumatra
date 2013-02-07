"""
Utility functions for use in publishing modules


"""

import os
import errno
from urllib import urlretrieve
from urlparse import urlparse
from sumatra.projects import load_project
from sumatra.recordstore import get_record_store
from sumatra.datastore import DataKey


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def determine_project(sumatra_options):
    if 'project_dir' in sumatra_options:
        prj = load_project(sumatra_options['project_dir'])
    elif os.path.exists(os.path.join('.smt', 'project')):
        prj = load_project()
    else:
        prj = None
    return prj


def determine_record_store(prj, sumatra_options, err=Exception):
    if 'record_store' in sumatra_options:
        record_store = get_record_store(sumatra_options["record_store"])
    elif prj is None:
        raise err(
            'Neither project_dir nor record_store defined'
        )
    else:
        record_store = prj.record_store
    return record_store


def determine_project_name(prj, sumatra_options, err=Exception):
    # determine the project (short) name
    if 'project' in sumatra_options:
        project_name = sumatra_options['project']
    elif prj is None:
        raise err('project name not defined')
    else:
        project_name = prj.name
    return project_name


def get_image_uri(record, sumatra_options, err=Exception):
    image_file = record.output_data[0]
    assert isinstance(image_file, DataKey), type(image_file)
    
    # check digest, if supplied
    if 'digest' in sumatra_options:
        if sumatra_options['digest'] != image_file.digest:
            raise err('Digests do not match')  # should also calculate digest of the actually-downloaded file
    
    if hasattr(image_file, 'url'):
        image_uri = image_file.url
    else:
        image_uri = "http://data.andrewdavison.info/Destexhe_JCNS_2009/" + image_file.path  ## temporary hack
        #raise NotImplementedError  # get file content, write local temporary file
    return image_uri


def download_to_local_directory(image_uri):
    # should probably use DataStore interface to do this, but just using urlretrieve for now
    local_image_cache = "smt_images"  # should use tempfile?
    remote_filename = os.path.basename(urlparse(image_uri).path)
    local_filename = os.path.join(local_image_cache, remote_filename)
    if not os.path.exists(local_filename):
        mkdir(local_image_cache)  
        urlretrieve(image_uri, local_filename)
    return local_filename


def record_link_url(server_url, project_name, record_label):
    return "%s%s/%s/" % (server_url, project_name, record_label)
