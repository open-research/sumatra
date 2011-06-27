"""
Decorators to make it easier to use Sumatra in your own Python scripts.

Usage:

@capture
def main(parameters, [other_args...]):
    <body of main function>
"""

import time
from sumatra.programs import PythonExecutable
import sys
import os

def capture(main):
    """
    Decorator for a main() function, which will create a new record for this
    execution. The first argument of main() must be a parameter set.
    """
    def wrapped_main(parameters, *args, **kwargs):
        import sumatra.projects
        project = sumatra.projects.load_project()
        main_file = os.path.abspath(sys.modules['__main__'].__file__)
        executable = PythonExecutable(path=sys.executable)
        record = project.new_record(parameters=parameters,
                                    main_file=main_file,
                                    executable=executable)
        parameters.update({"sumatra_label": record.label})
        start_time = time.time()
        main(parameters, *args, **kwargs)
        record.duration = time.time() - start_time
        record.data_keys = record.datastore.find_new_files(record.timestamp)
        project.add_record(record)
        project.save()
    return wrapped_main
