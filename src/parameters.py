from __future__ import with_statement
import os.path
from NeuroTools.parameters import ParameterSet as NTParameterSet

class SimpleParameterSet(object):
    
    def __init__(self, initialiser):
        self.values = {}
        self.types = {}
        if os.path.exists(initialiser):
            with open(initialiser) as f:
                content = f.readlines()
        else:
            content = initialiser.split("\n")
        for line in content:
            if "=" in line:
                name, value = line.split("=")[:2]
                self.values[name] = eval(value)
                self.types[name] = type(self.values[name])
    
    def __str__(self):
        return self.pretty()
    
    def pretty(self, expand_urls=False):
        output = []
        for name, value in self.values.items():
            type = self.types[name]
            if issubclass(type, basestring):
                output.append('%s = "%s"' % (name, value))
            else:
                output.append('%s = %s' % (name, value))
        return "\n".join(output)
    
    def as_dict(self):
        return self.values.copy()
    
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.pretty())

def build_parameters(filename, cmdline):
    try:
        parameters = NTParameterSet(filename)
    except SyntaxError:
        parameters = SimpleParameterSet(filename)
    return parameters