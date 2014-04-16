"""

"""

import socket
import sys
import locale
import os
import signal
import subprocess
from .compatibility import urlopen, URLError


TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def have_internet_connection():
    """
    Not foolproof, but allows checking for an external connection with a short
    timeout, before trying socket.gethostbyname(), which has a very long
    timeout.
    """
    test_address = 'http://74.125.113.99'  # google.com
    try:
        response = urlopen(test_address, timeout=1)
        return True
    except (URLError, socket.timeout) as err:
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
    return p.returncode, stdout, stderr


def _get_process_children(pid):
    p = subprocess.Popen('ps --no-headers -o pid --ppid %d' % pid, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]
