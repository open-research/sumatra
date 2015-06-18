"""


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import unicode_literals

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


def save_dependencies(cmd, filename):
    ''' save all dependencies to the file in the current folder '''
    file_dep = "depfun %s -toponly -quiet -print depfun.data;" %filename # save dependencies to a file
    mat_args = cmd.split('-r ')[-1]
    cmd = "%s; %s quit" %(mat_args, file_dep)
    p = subprocess.Popen(['matlab','-nodesktop', '-nosplash', '-nojvm', ' -nodisplay', '-wait', '-r', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)    
    result = p.wait()
    output = p.stdout.read() 
    # import pdb; pdb.set_trace() 
    return result, output


def find_dependencies(filename, executable):
    #ifile = os.path.join(os.getcwd(), 'depfun.data')
    file_data = (open('depfun.data', 'r'))
    content = file_data.read()
    paths = re.split('1: ', content)[2:]
    list_deps = []
    for path in paths:
        if os.name == 'posix':
            list_data = path.split('/')
        else:
            list_data = path.split('\\')
        list_deps.append(Dependency(list_data[-2], path.split('\n')[0]))
    file_data.close() # TODO: find version of external toolboxes
    return list_deps
