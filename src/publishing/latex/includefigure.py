"""

"""

import sys
import os
import errno
from ConfigParser import SafeConfigParser
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


def main(argv):
    config = SafeConfigParser()
    config.read(argv[0])
    sumatra_options = dict(config.items("sumatra"))
    graphics_options = dict(config.items("graphics"))
    
    # determine which record store to use
    if 'project_dir' in sumatra_options:
        prj = load_project(sumatra_options['project_dir'])
    elif os.path.exists(os.path.join('.smt', 'project')):
        prj = load_project()
    else:
        prj = None
    if 'record_store' in sumatra_options:
        record_store = get_record_store(sumatra_options["record_store"])
    elif prj is None:
        raise Exception(
            'Neither project_dir nor record_store defined'
        )
    else:
        record_store = prj.record_store
    
    # determine the project (short) name
    if 'project' in sumatra_options:
        project_name = sumatra_options['project']
    elif prj is None:
        raise Exception('project name not defined')
    else:
        project_name = prj.name
    
    record_label = sumatra_options['label']
    record = record_store.get(project_name, record_label)
    image_file = record.output_data[0]
    assert isinstance(image_file, DataKey), type(image_file)
    
    # check digest, if supplied
    if 'digest' in sumatra_options:
        if sumatra_options['digest'] != image_file.digest:
            raise Exception('Digests do not match')  # should also calculate digest of the actually-downloaded file
    
    if hasattr(image_file, 'url'):
        image_uri = image_file.url
    else:
        image_uri = "http://data.andrewdavison.info/Destexhe_JCNS_2009/" + image_file.path  ## temporary hack
        #raise NotImplementedError  # get file content, write local temporary file
     
    # download the file to a temporary directory
    # should probably use DataStore interface to do this, but just using urlretrieve for now
    local_image_cache = "smt_images"
    remote_filename = os.path.basename(urlparse(image_uri).path)
    local_filename = os.path.join(local_image_cache, remote_filename)
    if not os.path.exists(local_filename):
        mkdir(local_image_cache)  
        urlretrieve(image_uri, local_filename)
    include_graphics_cmd = "\includegraphics"
    if graphics_options:
        include_graphics_cmd += "[%s]" % ",".join("%s=%s" % item for item in graphics_options.items())
    include_graphics_cmd += "{%s}" % local_filename
    
    # if record_store is web-accessible, wrap the image in a hyperlink
    if hasattr(record_store, 'server_url'):
        target = "%s%s/%s/" % (record_store.server_url, project_name, record_label)
        cmd = "\href{%s}{%s}" % (target, include_graphics_cmd)
    else:
        cmd = include_graphics_cmd
        
    print cmd



if __name__ == '__main__':
    main(sys.argv[1:])