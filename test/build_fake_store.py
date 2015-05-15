from builtins import range
from sumatra.projects import Project
from sumatra.records import Record
from sumatra.recordstore import django_store
from sumatra.programs import PythonExecutable
from sumatra.launch import SerialLaunchMode
from sumatra.datastore import FileSystemDataStore
from sumatra.parameters import SimpleParameterSet
from sumatra.versioncontrol._git import GitRepository
import random

serial = SerialLaunchMode()
executable = PythonExecutable("/usr/bin/python", version="2.7")
repos = GitRepository('.')
datastore = FileSystemDataStore("/path/to/datastore")
project = Project("test_project",
                  default_executable=executable,
                  default_repository=repos,
                  default_launch_mode=serial,
                  data_store=datastore,
                  record_store=django_store.DjangoRecordStore())
parameters = SimpleParameterSet({'a': 2, 'b': 3})

for i in range(50):
    record = Record(executable=executable, repository=repos,
                    main_file="main.py", version="99863a9dc5f",
                    launch_mode=serial, datastore=datastore,
                    parameters=parameters, input_data=[], script_arguments="",
                    label="fake_record%00d" % i,
                    reason="testing", diff='', user='michaelpalin',
                    on_changed='store-diff', stdout_stderr='srgvrgvsgverhcser')
    record.duration = random.gammavariate(1.0, 1000.0)
    record.outcome = "lghsvdghsg zskjdcghnskdjgc ckdjshcgndsg"
    record.data_key = "['output.data']"
    record.dependencies = []
    record.platforms = serial.get_platform_information()
    project.add_record(record)
