#!/usr/bin/env python
# encoding: utf-8
# Author: sorin sbarnea
# License: public domain

import logging, sys, signal, subprocess, types, os, codecs, platform
try:
    from time import process_time
except ImportError:  # Python 2.7 fallback
    from time import clock as process_time

string_types = str,

global logger
global stdout
global stderr
global timing
global log_command

logger = None
stdout = False
stderr = False
timing = True # print execution time of each command in the log, just after the return code
log_command = True # outputs the command being executed to the log (before command output)
_sentinel = object()

def quote_command(cmd):
        """
        This function does assure that the command line is entirely quoted.
        This is required in order to prevent getting "The input line is too long" error message.
        """
        if not (os.name == "nt" or os.name == "dos"):
                return cmd # the escaping is required only on Windows platforms, in fact it will break cmd line on others

        import re
        re_quoted_items = re.compile(r'" \s* [^"\s] [^"]* \"', re.VERBOSE)
        woqi = re_quoted_items.sub('', cmd)
        if len(cmd) == 0 or (len(woqi) > 0 and not (woqi[0] == '"' and woqi[-1] == '"')):
                return '"' + cmd + '"'
        else:
                return cmd


def system3(cmd):
    import tempfile

    tf = tempfile.NamedTemporaryFile(mode="w+")
    result = os.system(cmd+" 2>&1 | tee %s" % tf.name)
    tf.flush()
    tf.seek(0)
    stdout_stderr = tf.readlines()
    tf.close()
    return result, stdout_stderr

def system2(cmd, cwd=None, logger=_sentinel, stdout=_sentinel, log_command=_sentinel, timing=_sentinel, capture_stderr=True):
        #def tee(cmd, cwd=None, logger=tee_logger, console=tee_console):
        """ This is a simple placement for os.system() or subprocess.Popen()
        that simulates how Unix tee() works - logging stdout/stderr using logging

        If you specify file (name or handler) it will output to this file.

        For filenames, it will open them as text for append and use UTF-8 encoding

        logger parameter can be:
        * 'string' - it will assume it is a filename, open it and log to it
        * 'handle' - it just write to it
        * 'function' - it call it using the message
        * None - disable any logging

        If logger parameter is not specified it will use python logging module.

        This method return (returncode, output_lines_as_list)

        """
        t = process_time()
        output = []
        if log_command is _sentinel: log_command = globals().get('log_command')
        if timing is _sentinel: timing = globals().get('timing')

        if logger is _sentinel: # default to python native logger if logger parameter is not used
                logger = globals().get('logger')
        if stdout is _sentinel:
                stdout = globals().get('stdout')

        #logging.debug("logger=%s stdout=%s" % (logger, stdout))

        f = sys.stdout
        ascii_aliases = ('ascii', 'ANSI_X3.4-1968')
        if not hasattr(f, 'encoding') or not f.encoding or f.encoding in ascii_aliases:
        # `ascii` is not a valid encoding by our standards, it's better to output to UTF-8 because it can encoding any Unicode text
                encoding = 'utf_8'
        else:
                encoding = f.encoding

        def filelogger(msg):
                try:
                        msg = msg + '\n'  # we'll use the same endline on all platforms, you like it or not
                        try:
                                f.write(msg)
                        except TypeError:
                                f.write(msg.encode("utf-8"))
                except Exception as e:
                        import traceback
                        print('        ****** ERROR: Exception: %s\nencoding = %s' % (e, encoding))
                        traceback.print_exc(file=sys.stderr)
                        sys.exit(-1)
                pass

        def nop(msg):
                pass

        if not logger:
                mylogger = nop
        elif isinstance(logger, string_types):
                f = codecs.open(logger, "a+b", 'utf_8')
                mylogger = filelogger
        elif isinstance(logger, (types.FunctionType, types.MethodType, types.BuiltinFunctionType)):
                mylogger = logger
        else:
                method_write = getattr(logger, "write", None)
                # if we can call write() we'll aceppt it :D
                if hasattr(method_write,'__call__'): # this should work for filehandles
                        f = logger
                        mylogger = filelogger
                else:
                        sys.exit("tee() does not support this type of logger=%s" % type(logger))

        if cwd is not None and not os.path.isdir(cwd):
                os.makedirs(cwd) # this throws exception if fails

        if capture_stderr:
                stderr = subprocess.STDOUT
        else:
                stderr = False

        # samarkanov: commented 'quote_command' deliberately
        # reason: if I have 'quote_command' Sumatra does not work in Windows (it encloses the command in quotes. I did not understand why should we quote)
        # I have never catched "The input line is too long" (yet?)
        # cmd = quote_command(cmd)
        if(log_command):
                mylogger("Running: %s" % cmd)
        completed_command = subprocess.run(cmd, cwd=cwd, shell=False, stdout=subprocess.PIPE, stderr=stderr, close_fds=(platform.system() == 'Linux'));
        returncode = completed_command.returncode
        output = completed_command.stdout
        if(log_command):
                if(timing):
                        def secondsToStr(t):
                                from functools import reduce
                                return "%02d:%02d:%02d" % reduce(lambda ll,b : divmod(ll[0],b) + ll[1:], [(t*1000,),1000,60,60])[:3]
                        mylogger("Returned: %d (execution time %s)\n" % (returncode, secondsToStr(process_time()-t)))
                else:
                        mylogger("Returned: %d\n" % (returncode))

        if not returncode == 0: # running a tool that returns non-zero? this deserves a warning
                logging.warning("Returned: %d from: %s\nOutput %s" % (returncode, cmd, output))

        return(returncode, output)

def system(cmd, cwd=None, logger=None, stdout=None, log_command=_sentinel, timing=_sentinel):
        """ System does not return a tuple """
        (returncode, output) = system2(cmd, cwd=cwd, logger=logger, stdout=stdout, log_command=log_command, timing=timing)
        return(returncode)

if __name__ == '__main__':
        import colorer
        import tempfile, os

        logging.basicConfig(level=logging.NOTSET,
                format='%(message)s')

        # default (stdout)
        print("#1")
        system("python --version")

        # function/method
        print("#2")
        system("python --version", logger=logging.error)

        # function (this is the same as default)
        print("#3")
        system("python --version", logger=print)

        # handler
        print("#4")
        f = tempfile.NamedTemporaryFile()
        system("python --version", logger=f)
        f.close()

        # test with string (filename)
        print("#5")
        (f, fname) = tempfile.mkstemp()
        system("python --version", logger=fname)
        os.close(f)
        os.unlink(fname)

        print("#6")
        stdout = False
        logger = None
        system("echo test")

        print("#7")
        stdout = True
        system("echo test2")
