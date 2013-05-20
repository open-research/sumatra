"""

"""

import sys
import os
import logging
try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser
from sumatra.publishing.utils import determine_project, determine_record_store, \
                                     determine_project_name, get_image, \
                                     record_link_url, get_record_label_and_image_path


logger = logging.getLogger("Sumatra")
logging.basicConfig(filename='sumatra.log', filemode='w', level=logging.INFO)

LOCAL_IMAGE_CACHE = "smt_images"  # should use tempfile?


def generate_latex_command(sumatra_options, graphics_options):
    # determine project and record store to use
    prj = determine_project(sumatra_options)
    record_store = determine_record_store(prj, sumatra_options)
    project_name = determine_project_name(prj, sumatra_options)    
    logger.info("Project name: %s", project_name)
    logger.info("Record store: %s", record_store)
    
    # get record, obtain image uri
    record_label, image_path = get_record_label_and_image_path(sumatra_options['label'])
    record = record_store.get(project_name, record_label)
    image = get_image(record, image_path, sumatra_options)  # automatically checks digest
    logger.info("Record: %s", record_label)
    logger.info("Image: %s", image)
    # download the image to a temporary directory
    if not os.path.exists(LOCAL_IMAGE_CACHE):
        os.makedirs(LOCAL_IMAGE_CACHE)
    local_filename = image.save_copy(LOCAL_IMAGE_CACHE)

    include_graphics_cmd = "\includegraphics"
    if graphics_options:
        include_graphics_cmd += "[%s]" % ",".join("%s=%s" % item for item in graphics_options.items())
    include_graphics_cmd += "{%s}" % local_filename
    
    # if record_store is web-accessible, wrap the image in a hyperlink
    if hasattr(record_store, 'server_url'):
        target = record_link_url(record_store.server_url, project_name, record_label)
        cmd = "\href{%s}{%s}" % (target, include_graphics_cmd)
    else:
        cmd = include_graphics_cmd
        
    print(cmd)


def read_config(filename):
    config = SafeConfigParser()
    config.read(filename)
    return dict(config.items("sumatra")), dict(config.items("graphics"))


if __name__ == '__main__':
    generate_latex_command(*read_config(sys.argv[1]))