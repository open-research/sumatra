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
try:
    import json
except ImportError:
    import simplejson as json

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
        dict_initializer = False
        try:
            if isinstance(eval(initialiser), dict):
                dict_initializer = True
                initialiser = eval(initialiser)
        except SyntaxError:
            pass

        if dict_initializer:
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
                    parts = line.split("=")
                    name = parts[0].strip()
                    value = "=".join(parts[1:])
                    if "#" in value:
                        value, comment = value.split("#")[:2]
                        self.comments[name] = comment
                    try:
                        self.values[name] = eval(value)
                    except (NameError, SyntaxError):
                        self.values[name] = unicode(value)
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
        exec_python = True # as a default Python is the executable
        from projects import load_project
        prj = load_project()
        if 'matlab' in prj.default_executable.path.lower():
            exec_python = False
        for name, value in self.values.items():
            type = self.types[name]
            if exec_python:
                if issubclass(type, basestring):
                    output.append('%s = "%s"' % (name, value))
                else:
                    output.append('%s = %s' % (name, value))
                if name in self.comments:
                    output[-1] += ' #%s' % self.comments[name]
            else: # if it isn't Python we will always have type = string (see SimpleParameterSet() SyntaxError)
                output.append('%s = %s' % (name, value))
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
                input = StringIO(str(initialiser)) # configparser has some problems with unicode. Using str() is a crude, and probably partial fix.
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
        elif self.has_option("sumatra", name):
            return self.get("sumatra", name)
        else:
            return dict(self.items(name))

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __deepcopy__(self, memo):
        # deepcopy of a SafeConfigParser fails under Python 2.7, so we
        # implement this simple version which avoids copying SRE_Pattern objects
        return ConfigParserParameterSet(self.pretty())

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
            else:
                section = "sumatra" # used for extra parameters added by sumatra
                option = name
            if not self.has_section(section):
                self.add_section(section)
            if not isinstance(value, basestring):
                value = str(value)
            self.set(section, option, value)
        if hasattr(E, "items"):
            for name,value in E.items():
                _update(name, value)
        else:
            for name, value in E:
                _update(name, value)
        for name,value in F.items():
            _update(name, value)

    def pop(self, name, d=None):
        if "." in name:
            section, option = name.split(".")
            value = self.get(section, option)
            self.remove_option(section, option)
            return value
        elif self.has_option("sumatra", name):
            value = self.get("sumatra", name)
            self.remove_option("sumatra", name)
        # should we allow popping an entire section?
        else:
            value = d
        return value


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
        self.values.update(E, **F)

    def pop(self, key, d=None):
        if key in self.values:
            return self.values.pop(key)
        else:
            return d


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
