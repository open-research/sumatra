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
                name = name.strip()
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

    def update(self, name, value):
        self.values[name] = value
        self.types[name] = type(value)
        

def build_parameters(filename, cmdline_parameters):
    try:
        parameters = NTParameterSet(filename)
    except SyntaxError:
        parameters = SimpleParameterSet(filename)
    for p in cmdline_parameters:
        name, value = p.split("=")
        for cast in int, float:
            try:
                value = cast(value)
                break
            except ValueError:
                pass
        parameters.update(name, value)
    return parameters