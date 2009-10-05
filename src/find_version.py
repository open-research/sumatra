from __future__ import with_statement
from types import ModuleType

def find_version(module):
    version = 'unknown'
    for attr_name in 'version', 'get_version', '__version__', 'VERSION':
        if hasattr(module, attr_name):
            attr = getattr(module, attr_name)
            if callable(attr):
                version = attr()
            elif isinstance(attr, ModuleType):
                version, _ = find_version(attr)
                attr_name += '.' + _
            else:
                version = attr
            break
    # next, check if the module is a .egg
    if version == 'unknown':
        dir = os.path.dirname(module.__file__)
        if 'EGG-INFO' in os.listdir(dir):
            with open(os.path.join(dir, 'EGG-INFO', 'PKG-INFO')) as f:
                for line in f.readlines():
                    if line[:7] == 'Version':
                        version = line.split(' ')[1].strip()
                        attr_name = 'egg-info'
                        break
    # next, could check for an egg-info file with a similar name to the module
    # although this is not really safe, as there can be old egg-info files
    # lying around.
    return version, attr_name

import os

def test():
    for file in os.listdir('/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/'):
        ext = os.path.splitext(file)[1]
        if ext == '' or ext == '.egg':
            file = file.split('-')[0]
            try:
                m = __import__(file)
                print file, find_version(m)[0]
            except ImportError:
                pass
        