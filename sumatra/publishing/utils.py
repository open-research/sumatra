"""
Utility functions for use in publishing modules


"""

import os
import errno
from ..compatibility import urlretrieve, urlparse
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
    if 'project_dir' in sumatra_options and sumatra_options['project_dir']:
        prj = load_project(sumatra_options['project_dir'])
    elif os.path.exists(os.path.join('.smt', 'project')):
        prj = load_project()
    else:
        prj = None
    return prj


def determine_record_store(prj, sumatra_options, err=Exception):
    if 'record_store' in sumatra_options and sumatra_options["record_store"]:
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
    if 'project' in sumatra_options and sumatra_options['project']:
        project_name = sumatra_options['project']
    elif prj is None:
        raise err('project name not defined')
    else:
        project_name = prj.name
    return project_name


def get_record_label_and_image_path(ref):
    if '?' in ref:
        parts = ref.split("?")
        if len(parts) == 2:
            record_label, image_path =  parts
            image_path = "?" + image_path
        else:
            raise Exception("Invalid record/path query")
    elif ':' in ref:
        parts = ref.split(":")
        if len(parts) == 2:
            record_label, image_path =  parts
        else:
            raise Exception("Invalid record/path reference")
    else:
        record_label, image_path =  ref, None
    return record_label, image_path


def get_image(record, image_path, sumatra_options, err=Exception):
    if image_path is None:
        image_key = record.output_data[0]
    else:
        image_key = None
        if image_path.startswith("?"):
            for key in record.output_data:
                if image_path[1:] in key.path:
                    image_key = key
                    break
        else:
            for key in record.output_data:
                if key.path == image_path:
                    image_key = key
                    break
        if image_key is None:
            raise ValueError("Record %s has no output data file with path %s. Valid paths are: %s" % (
                    record.label, image_path, ", ".join(key.path for key in record.output_data)))
    assert isinstance(image_key, DataKey)
    # check expected digest, if supplied, against key.digest
    if ('digest' in sumatra_options
        and sumatra_options['digest'] != image_key.digest):
        raise err('Digests do not match')
    return record.datastore.get_data_item(image_key)  # checks key.digest against file contents


def record_link_url(server_url, project_name, record_label):
    return "%s%s/%s/" % (server_url, project_name, record_label)
