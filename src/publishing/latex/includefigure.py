"""

"""

import sys
from ConfigParser import SafeConfigParser
from sumatra.publishing.utils import determine_project, determine_record_store, \
                                     determine_project_name, get_image_uri, \
                                     download_to_local_directory, record_link_url


def generate_latex_command(sumatra_options, graphics_options):
    # determine project and record store to use
    prj = determine_project(sumatra_options)
    record_store = determine_record_store(prj, sumatra_options)
    project_name = determine_project_name(prj, sumatra_options)    
    
    # get record, obtain image uri
    record_label = sumatra_options['label']
    record = record_store.get(project_name, record_label)
    image_uri = get_image_uri(record, sumatra_options)
    
    # download the image to a temporary directory
    local_filename = download_to_local_directory(image_uri)

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
        
    print cmd


def read_config(filename):
    config = SafeConfigParser()
    config.read(filename)
    return dict(config.items("sumatra")), dict(config.items("graphics"))


if __name__ == '__main__':
    generate_latex_command(*read_config(argv[1]))