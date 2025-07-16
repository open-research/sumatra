"""


:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import os
import re
import subprocess
from sumatra.dependency_finder import core


class Dependency(core.BaseDependency):
    """
    Contains information about a Matlab toolbox.
    """
    module = 'matlab'
    
    def __init__(self, module_name, path, version='unknown', diff='', source=None):
        super(Dependency, self).__init__(module_name, path, version, diff, source)


def find_dependencies(filename, executable):
    #ifile = os.path.join(os.getcwd(), 'depfun.data')
    with open('depfun.data', 'r') as file_data:
        content = file_data.read()
        paths = re.split('1: ', content)[2:]
        list_deps = []
        for path in paths:
            if os.name == 'posix':
                list_data = path.split('/')
            else:
                list_data = path.split('\\')
            list_deps.append(Dependency(list_data[-2], path.split('\n')[0]))
    # TODO: find version of external toolboxes
    return list_deps
