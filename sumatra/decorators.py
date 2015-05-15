"""
Decorators to make it easier to use Sumatra in your own Python scripts.

Usage:

@capture
def main(parameters, [other_args...]):
    <body of main function>


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import time
from sumatra.programs import PythonExecutable
import sys
import os
import contextlib
from io import StringIO


@contextlib.contextmanager
def _grab_stdout_stderr():
    try:
        output = StringIO()
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
