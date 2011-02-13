"""
Export a Sumatra RecordStore for version 0.1 to JSON.
"""

try:
    import json
except ImportError:
    import simplejson as json
from sumatra import __version__, projects
from sumatra.recordstore.shelve_store import ShelveRecordStore
from sumatra.recordstore.django_store import DjangoRecordStore
import sys
import os

if __version__ != "0.1":
    print "Must use Sumatra 0.1"
    sys.exit(1)

def load_recordstore():
    try:
        store = ShelveRecordStore(".smt/simulation_records")
    except Exception:
        store = DjangoRecordStore(".smt/simulation_records")
    return store

def encode_record(record, indent=None):
    data = {
        "SUMATRA_VERSION": 0.1,
        "label": record.label,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": record.reason,
        "duration": record.duration,
        "executable": {
            "path": record.executable.path,
            "version": record.executable.version,
            "name": record.executable.name,
         },
        "repository": {
            "url": record.repository.url,
            "type": record.repository.__class__.__name__,
        },
        "main_file": record.main_file,
        "version": record.version,
        "parameters": {
            "content": str(record.parameters),
            "type": record.parameters.__class__.__name__,
        },
        "launch_mode": {
            "type": record.launch_mode.__class__.__name__, 
            "parameters": str(record.launch_mode.get_state()),
        },
        "datastore": {
            "type": record.datastore.__class__.__name__,
            "parameters": str(record.datastore.get_state()),
        },
        "outcome": record.outcome or "",
        "data_key": str(record.data_key),
        "tags": list(record.tags) + [record.group],
        "diff": record.diff,
        "dependencies": [{
            "path": d.path,
            "version": d.version,
            "name": d.name,
            "module": d.module,
            "diff": d.diff,
            } for d in record.dependencies],
        "platforms": [{
            "system_name": p.system_name, 
            "ip_addr": p.ip_addr, 
            "architecture_bits": p.architecture_bits, 
            "machine": p.machine, 
            "architecture_linkage": p.architecture_linkage, 
            "version": p.version, 
            "release": p.release, 
            "network_name": p.network_name, 
            "processor": p.processor
            } for p in record.platforms],
        }
    return data

def export_records(output_file):
    store = load_recordstore()
    patch_sumatra()
    f = open(output_file, 'w')
    json.dump([encode_record(record) for record in store.list(groups=None)],
              f, indent=2)
    f.close()

def patch_sumatra():
    import sumatra.programs
    import sumatra.recordstore.django_store.models
    import sumatra.versioncontrol.base
    sumatra.programs.Executable._find_executable = lambda self, name: name
    def repos_to_sumatra(self):
        cls = type(str(self.type), (sumatra.versioncontrol.base.Repository,), {})
        return cls(self.url)
    sumatra.recordstore.django_store.models.Repository.to_sumatra = repos_to_sumatra #patch for Michele Mattioni, who started using GitRepository

def _get_class_path(obj):
    return obj.__class__.__module__ + "." + obj.__class__.__name__

def export_project(output_file):
    prj = projects.load_simulation_project()
    state = {
        'name': prj.name,
        'on_changed': prj.on_changed,
        'default_main_file': prj.default_main_file,
        'default_executable': None,
        'default_repository': None,
        'default_launch_mode': None,
        'data_store': dict(prj.data_store.get_state(),
                           type=_get_class_path(prj.data_store)),
        'record_store': dict(type=_get_class_path(prj.record_store)),
        'description': "", # not in 0.1
        'data_label': None, # not in 0.1
        '_most_recent': "", # not in 0.1
    }
    if prj.default_executable:
        obj = prj.default_executable
        state['default_executable'] = {
            'type': _get_class_path(obj), 'path': obj.path,
            'version': obj.version
        }
    if prj.default_repository:
        obj = prj.default_repository
        state['default_repository'] = {
            'type': _get_class_path(obj), 'url': obj.url,
        }
    if prj.default_launch_mode:
        obj = prj.default_launch_mode
        state['default_launch_mode'] = dict(obj.get_state(),
                                       type=_get_class_path(obj))
    if prj.record_store.__class__.__name__[:6] == 'Django':
        state['record_store']['db_file'] = ".smt/records" #prj.record_store._db_file
    else:
        state['record_store']['shelf_name'] = ".smt/records" #prj.record_store._shelf_name
    f = open(output_file, 'w')
    json.dump(state, f, indent=2)
    f.close()

if __name__ == "__main__":
    export_records(".smt/records_export.json")
    export_project(".smt/project_export.json")
