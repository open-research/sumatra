"""


:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import socket
import sys
import locale
import os
import signal
import subprocess
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import URLError
import re


# Note: This is the format that is used in creating labels,
#       it is _not_ the format used in serializing to/from JSON,
#       which includes time-zone information.
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"

STATUS_FORMAT = "_%s_"
STATUS_PATTERN = re.compile(r"_(([^.]*)(\.\.\.)?)_")


def have_internet_connection():
    """
    Not foolproof, but allows checking for an external connection with a short
    timeout, before trying socket.gethostbyname(), which has a very long
    timeout.
    """
    test_address = 'http://74.125.113.99'  # google.com
    try:
        urlopen(test_address, timeout=1)
        return True
    except (URLError, socket.timeout):
        pass
    return False


def get_encoding():
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        encoding = sys.stdout.encoding
    else:
        encoding = locale.getpreferredencoding()
        if encoding == '':  # getpreferredencoding does not guarantee to return an encoding
            encoding = sys.getdefaultencoding()
    return encoding


def run(args, cwd=None, shell=False, kill_tree=True, timeout=None, env=None):
    """
    Run a command with a timeout.
    """

    completed_command = subprocess.run(args, shell=shell, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout)
    stdout = completed_command.stdout
    stdout = stdout.decode(get_encoding())
    stderr = completed_command.stderr
    stderr = stderr.decode(get_encoding())
    return completed_command.returncode, str(stdout), str(stderr)


def _get_process_children(pid):
    completed_command = subprocess.run(['ps','--no-headers', '-o', 'pid', '--ppid', pid], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = completed_command.stdout
    return [int(child_pid) for child_pid in stdout.split()]


class SingletonType(type):
    """A meta class that creates classes applying the singleton pattern."""

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance


class _Registry(metaclass=SingletonType):

    def __init__(self):
        self._components = {}

    def add_component_type(self, base_class):
        if not hasattr(base_class, 'required_attributes'):
            raise TypeError("Component type {0} is missing attribute 'required_attributes'."
                            .format(base_class))
        self._components[base_class] = OrderedDict()

    @property
    def components(self):
        return self._components

    def register(self, component):
        for base_class in self._components:
            if issubclass(component, base_class):
                for attr in base_class.required_attributes:
                    if not hasattr(component, attr):
                        raise TypeError("%s is missing required attribute %s" % (component, attr))
                if hasattr(component, "name"):
                    names = [component.name]
                elif hasattr(component, "names"):
                    names = component.names
                else:
                    names = [component.__name__]
                for name in names:
                    self._components[base_class][name] = component
                return
        raise TypeError("%s is not a Sumatra component." % component)


def component_type(cls):
    """Class decorator to define base types for components.

    Use this decorator to register a base type of a Sumatra component. Concrete components
    should subclass from this component type to then be registered as a Sumatra component.

    Not to be used when writing Sumatra plug-ins! For that, please use the `component`
    decorator.

    Example:
    @component_type
    class MyComponentBase(object):
        pass

    @component
    class MyConcreteComponent(MyComponentBase):
        pass
    """
    for base_type in _Registry().components:
        if issubclass(cls, base_type):
            msg = "{cls} is a subclass of already registered component type {base} and " \
                  "hence could not be registered as component type." \
                  .format(**{'cls': cls, 'base': base_type})
            raise TypeError(msg)
    _Registry().add_component_type(cls)
    return cls


def component(cls):
    """Class decorator to define Sumatra components.

    Use this decorator to declare a class as a Sumatra component. It can then be used
    by Sumatra.
    """
    _Registry().register(cls)
    return cls


def conditional_component(condition):
    """Class decorator to define Sumatra components based on a condition.

    Similar to `component`, this decorator can be used to declare a class as a Sumatra
    component. In addition to the former, a condition defines whether that component
    will be used by Sumatra or not.

    Example:
    try:
        import NumPy
    except ImportError:
        have_numpy = False
    else:
        have_numpy = True

    @conditional_component(condition=have_numpy)
    class MyNumPyComponent(MyNumPyComponentBase):
        pass
    """
    if condition is True:
        return component
    else:
        return lambda cls: cls  # identity function, do nothing


def get_registered_components(base_type):
    """Returns all registered components for the given component base type."""
    return _Registry().components[base_type]
