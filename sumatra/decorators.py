"""
Decorators to make it easier to use Sumatra in your own Python scripts.

Usage:

@capture
def main(parameters, [other_args...]):
    <body of main function>


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import unicode_literals

from builtins import str
import time
from sumatra.programs import PythonExecutable
from sumatra.parameters import SimpleParameterSet
import sys
import os
import contextlib
from io import StringIO


class _ByteAndUnicodeStringIO(StringIO):
    """A StringIO subclass accepting `str` in Py2 and `str` in Py3.

    The io.StringIO implementation does not accept Py2 `str`.
    """

    def write(self, object):
        StringIO.write(self, str(object))


@contextlib.contextmanager
def _grab_stdout_stderr():
    try:
        output = _ByteAndUnicodeStringIO()
        sys.stdout, sys.stderr = output, output
        yield output
    finally:
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        output = output.getvalue()


def capture(main):
    """
    Decorator for a main() function, which will create a new record for this
    execution. The first argument of main() must be a parameter set.
    """
    def wrapped_main(parameters, *args, **kwargs):
        import sumatra.projects
        project = sumatra.projects.load_project()
        main_file = sys.modules['__main__'].__file__
        executable = PythonExecutable(path=sys.executable)
        record = project.new_record(parameters=parameters,
                                    main_file=main_file,
                                    executable=executable)
        record.launch_mode.working_directory = os.getcwd()
        parameters.update({"sumatra_label": record.label})
        start_time = time.time()
        with _grab_stdout_stderr() as stdout_stderr:
            main(parameters, *args, **kwargs)
            record.stdout_stderr = stdout_stderr.getvalue()
        record.duration = time.time() - start_time
        record.output_data = record.datastore.find_new_data(record.timestamp)
        project.add_record(record)
        project.save()

    return wrapped_main

def capture_args(main):
    """
    Decorator for a main() function, which will create a new record for this
    execution.

    The arguments of main() will be considered the parameter set. This assumes
    all arguments are basic types (i.e. they get passed to SimpleParameterSet).
    """
    def wrapped_main(*args, **kwargs):
        parameters = dict(zip(["arg%d" % x for x in range(len(args))], args))
        parameters.update(kwargs)
        parameters = SimpleParameterSet(parameters)

        @capture
        def fake_main(param, *args, **kwargs):
            # Discard parameters
            main(*args, **kwargs)

        # Run the fake main to discard the parameters
        fake_main(parameters, *args, **kwargs)

    return wrapped_main
