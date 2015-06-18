"""


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import unicode_literals
from builtins import str
from future.standard_library import install_aliases
install_aliases()
from builtins import object
from future.utils import with_metaclass

import socket
import sys
import locale
import os
import signal
import subprocess
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import URLError
import warnings


TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


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


def run(args, cwd=None, shell=False, kill_tree=True, timeout=-1, env=None):
    """
    Run a command with a timeout after which it will be forcibly
    killed.

    Based on http://stackoverflow.com/a/3326559
    """
    class Alarm(Exception):
        pass

    def alarm_handler(signum, frame):
        raise Alarm
    p = subprocess.Popen(args, shell=shell, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, env=env)
    if timeout != -1:
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        stdout = stdout.decode(get_encoding())
        stderr = stderr.decode(get_encoding())
        if timeout != -1:
            signal.alarm(0)
    except Alarm:
        pids = [p.pid]
        if kill_tree:
            pids.extend(_get_process_children(p.pid))
        for pid in pids:
            # process might have died before getting to this line
            # so wrap to avoid OSError: no such process
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        return -9, '', ''
    return p.returncode, str(stdout), str(stderr)


def _get_process_children(pid):
    p = subprocess.Popen('ps --no-headers -o pid --ppid %d' % pid, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return [int(child_pid) for child_pid in stdout.split()]


class SingletonType(type):
    """A meta class that creates classes applying the singleton pattern."""

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance


class _Registry(with_metaclass(SingletonType, object)):

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
                    name = component.name
                else:
                    name = component.__name__
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
