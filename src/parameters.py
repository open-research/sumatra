"""
The parameters module handles different parameter file formats.

The original idea was that all parameter files will be converted to a single
internal parameter format, the NeuroTools ParameterSet class. This will allow
fancy searching/comparisons based on parameters. However, we don't do this at
the moment, the only methods that are used are `update()` and `save()

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
# JSONParameterSet and YAMLParameterSet should be useful and straightforward to
# implement. XMLParameterSet could also be useful, but is unlikely to be
# straightforward.

from __future__ import with_statement
import os.path
import shutil
from ConfigParser import SafeConfigParser, MissingSectionHeaderError
from cStringIO import StringIO
from sumatra.external import NeuroTools
import json

class NTParameterSet(NeuroTools.parameters.ParameterSet):
    # just a re-name, to clarify things
    pass


class SimpleParameterSet(object):
    """
    Handles parameter files in a simple "name = value" format, with no nesting or grouping.
    """
    
    def __init__(self, initialiser):
        """
        Create a new parameter set from a file or string. In both cases,
        parameters should be separated by newlines.
        """
        self.values = {}
        self.types = {}
        self.comments = {}
        if isinstance(initialiser, dict):
            for name, value in initialiser.items():
                self.values[name] = value
                self.types[name] = type(value)
        else:
            if os.path.exists(initialiser):
                with open(initialiser) as f:
                    content = f.readlines()
            else:
                content = initialiser.split("\n")
            for line in content:
                line = line.strip()
                if "=" in line:
                    name, value = line.split("=")[:2]
                    name = name.strip()
                    if "#" in value:
                        value, comment = value.split("#")[:2]
                        self.comments[name] = comment
                    self.values[name] = eval(value)
                    self.types[name] = type(self.values[name])   
                elif line:
                    if line.strip()[0] == "#":
                        pass
                    else:
                        raise SyntaxError("File is not a valid simple parameter file. This line caused the error: %s" % line)

    def __str__(self):
        return self.pretty()
    
    def __getitem__(self, name):
        return self.values[name]
    
    def __eq__(self, other):
        return ((self.values == other.values) and (self.types == other.types))
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def pop(self, k, d=None):
        if k in self.values:
            v = self.values.pop(k)
            self.types.pop(k)
            self.comments.pop(k, None)
            return v
        elif d:
            return d
        else:
            raise KeyError("%s not found" % k)
    
    def pretty(self, expand_urls=False):
        """
        Return a string representation of the parameter set, suitable for
        creating a new, identical parameter set.
        
        expand_urls is present for compatibility with NTParameterSet, and is
                    not used.
        """
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
        __doc__ = dict.update.__doc__
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


class ConfigParserParameterSet(SafeConfigParser):
    """
    Handles parameter files in traditional config file format, as parsed by the
    standard Python ConfigParser module. Note that this format does not
    distinguish numbers from string representations of those numbers, so all
    parameter values are treated as strings.
    """
    
    def __init__(self, initialiser):
        """
        Create a new parameter set from a file or string.
        """
        SafeConfigParser.__init__(self)
        try:
            if os.path.exists(initialiser):
                self.read(initialiser)
            else:
                input = StringIO(initialiser)
                input.seek(0)
                self.readfp(input)
        except MissingSectionHeaderError:
            raise SyntaxError("Initialiser contains no section headers")

    def __str__(self):
        return self.pretty()
    
    def __getitem__(self, name):
        if "." in name:
            section, option = name.split(".")
            return self.get(section, option)
        else:
            return dict(self.items(name))
    
    def __eq__(self, other):
        return self.as_dict() == other.as_dict()
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def pretty(self, expand_urls=False):
        """
        Return a string representation of the parameter set, suitable for
        creating a new, identical parameter set.
        
        expand_urls is present for compatibility with NTParameterSet, and is
                    not used.
        """
        output = StringIO()
        self.write(output)
        return output.getvalue()
    
    def as_dict(self):
        D = {}
        for section in self.sections():
            D[section] = dict(self.items(section))
        return D
    
    def save(self, filename):
        with open(filename, "w") as f:
            self.write(f)

    def update(self, E, **F):
        __doc__ = dict.update.__doc__
        def _update(name, value):
            if "." in name:
                section, option = name.split(".")
                if not self.has_section(section):
                    self.add_section(section)
                if not isinstance(value, basestring):
                    value = str(value)
                self.set(section, option, value)
            else:
                raise Exception("For the ConfigParserParameterSet, parameter names must be of the format 'section.parameter'")
        if hasattr(E, "items"):
            for name,value in E.items():
                _update(name, value)
        else:
            for name, value in E:
                _update(name, value)
        for name,value in F.items():
            _update(name, value)

class JSONParameterSet(object):
    """
    Handles parameter files in JSON format, as parsed by the
    standard Python json module.
    """
    
    def __init__(self, initialiser):
        """
        Create a new parameter set from a file or string.
        """
        try:
            if os.path.exists(initialiser):
                with open(initialiser) as fid:
                    self.values = json.load(fid)
            else:
                if initialiser:
                    self.values = json.loads(initialiser)
                else:
                    self.values = {}
        except ValueError:
            raise SyntaxError("Misformatted JSON file")

    def __str__(self):
        return self.pretty()
    
    def __getitem__(self, name):
        return self.values[name] 
    
    def __eq__(self, other):
        return self.as_dict() == other.as_dict()
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def pretty(self, expand_urls=False):
        """
        Return a string representation of the parameter set, suitable for
        creating a new, identical parameter set.
        
        expand_urls is present for compatibility with NTParameterSet, and is
                    not used.
        """
        
        output = json.dumps(self.values, sort_keys=True, indent=4)
        return output
    
    def as_dict(self):
        return self.values
    
    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.values, f)

    def update(self, E, **F):
        __doc__ = dict.update.__doc__
        self.value.update(E, **F)

def build_parameters(filename):
    
    try: 
        parameters = JSONParameterSet(filename)
        return parameters
    except SyntaxError:
        pass

    try:
        parameters = NTParameterSet("file://%s" % os.path.abspath(filename))
        return parameters 
    except (SyntaxError, NameError):
        pass
    
    try:
        parameters = ConfigParserParameterSet(filename)
        return parameters
    except SyntaxError:
        pass

    parameters = SimpleParameterSet(filename)
    return parameters
