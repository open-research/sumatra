"""


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from __future__ import unicode_literals
from builtins import str
from future.standard_library import install_aliases
install_aliases()
from builtins import object

import socket
import sys
import locale
import os
import signal
import subprocess
from collections import OrderedDict
from urllib.request import urlopen
from urllib.error import URLError


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


class Registry(object):

    def __init__(self):
        self.components = {}

    def add_component_type(self, base_class):
        self.components[base_class] = OrderedDict()

    def register(self, component):
        for base_class in self.components:
            if issubclass(component, base_class):
                for attr in base_class.required_attributes:
                    if not hasattr(component, attr):
                        raise TypeError("%s is missing required attribute %s" % (component, attr))
                if hasattr(component, "name"):
                    name = component.name
                else:
                    name = component.__name__
                self.components[base_class][name] = component
                return
        raise TypeError("%s is not a Sumatra component." % component)

registry = Registry()
