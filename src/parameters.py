"""
The parameters module handles different parameter file formats, taking care of
converting them to/from Sumatra's internal parameter format, which is the
NeuroTools ParameterSet class.

Classes
-------

NTParameterSet           - handles parameter files in the NeuroTools parameter
                           set format, based on nested dictionaries
SimpleParameterSet       - handles parameter files in a simple "name = value"
                           format, with no nesting or grouping.
ConfigParserParameterSet - handles parameter files in traditional config file
                           format, as parsed by the standard Python ConfigParser
                           module.
"""

from __future__ import with_statement
import os.path
import shutil
import re
from sumatra.external import NeuroTools

class NTParameterSet(NeuroTools.parameters.ParameterSet):
    # just a re-name, to clarify things
    pass

class SimpleParameterSet(object):
    
    def __init__(self, initialiser):
        self.values = {}
        self.types = {}
        self.comments = {}
        if os.path.exists(initialiser):
            with open(initialiser) as f:
                content = f.readlines()
        else:
            content = initialiser.split("\n")
        for line in content:
            if "=" in line:
                name, value = line.split("=")[:2]
                name = name.strip()
                if "#" in value:
                    value, comment = value.split("#")[:2]
                    self.comments[name] = comment
                self.values[name] = eval(value)
                self.types[name] = type(self.values[name])   
    
    def __str__(self):
        return self.pretty()
    
    def __getitem__(self, name):
        return self.values[name]
    
    def pretty(self, expand_urls=False):
        output = []
        for name, value in self.values.items():
            type = self.types[name]
            if issubclass(type, basestring):
                output.append('%s = "%s"' % (name, value))
            else:
                output.append('%s = %s' % (name, value))
            if name in self.comments:
                output[-1] += ' #%s' % self.comments[name]
        return "\n".join(output)
    
    def as_dict(self):
        return self.values.copy()
    
    def save(self, filename):
        if os.path.exists(filename):
            shutil.copy(filename, filename + ".orig")
        with open(filename, 'w') as f:
            f.write(self.pretty())

    def update(self, E, **F):
        def _update(name, value):
            if not isinstance(value, (int, float, basestring, list)):
                raise TypeError("value must be a numeric value or a string")
            self.values[name] = value
            self.types[name] = type(value)
        if hasattr(E, "items"):
            for name,value in E.items():
                _update(name, value)
        else:
            for name, value in E:
                _update(name, value)
        for name,value in F.items():
            _update(name, value)
            
        

list_pattern = re.compile(r'^\s*\[.*\]\s*$')
tuple_pattern = re.compile(r'^\s*\(.*\)\s*$')



def build_parameters(filename, cmdline_parameters=[]):
    try:
        parameters = NTParameterSet("file://%s" % os.path.abspath(filename))
    except SyntaxError:
        parameters = SimpleParameterSet(filename)
    for p in cmdline_parameters:
        name, value = p.split("=")
        if list_pattern.match(value) or tuple_pattern.match(value):
            value = eval(value)
        else:
            for cast in int, float:
                try:
                    value = cast(value)
                    break
                except ValueError:
                    pass
        parameters.update({name: value})
    return parameters