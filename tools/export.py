"""
Export a Sumatra project for version 0.1 or 0.2 to JSON.

:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import json
from sumatra import __version__, projects
from sumatra.recordstore.shelve_store import ShelveRecordStore
from sumatra.recordstore.django_store import DjangoRecordStore
import sys
import shutil

version = __version__.split(".")
major_version = int(version[0])
minor_version = int(version[1][0])
if major_version != 0 or minor_version not in (1, 2, 3):
    print("This script is only intended for use with Sumatra 0.1, 0.2, 0.2.1 or 0.3.0. You are using %s" % __version__)
    sys.exit(1)

STORE_FILE = {
    1: ".smt/simulation_records",
    2: ".smt/records",
    3: ".smt/records",
}


def load_recordstore():
    store_file = STORE_FILE[minor_version]
    try:
        store = ShelveRecordStore(store_file)
    except Exception:
        store = DjangoRecordStore(store_file)
    return store


def encode_record(record, indent=None):
    data = {
        "SUMATRA_VERSION": __version__,
        "label": record.label,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S%z"),
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
            "parameters": record.launch_mode.get_state(),
        },
        "datastore": {
            "type": record.datastore.__class__.__name__,
            "parameters": record.datastore.get_state(),
        },
        "outcome": record.outcome or "",
        "data_key": str(record.data_key),
        "tags": list(record.tags),
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
    if minor_version == 1:
        data["tags"] += [record.group]
    if minor_version == 2:
        data["user"] = record.user
    return data


def export_records(output_file):
    store = load_recordstore()
    if minor_version < 3:
        patch_sumatra()
    with open(output_file, 'w') as f:
        if minor_version == 1:
            json.dump([encode_record(record) for record in store.list(groups=None)],
                      f, indent=2)
        else:
            project_name = projects.load_project().name
            if minor_version == 2:
                json.dump([encode_record(record) for record in store.list(project_name)],
                          f, indent=2)
            else:
                f.write(store.export(project_name))


def patch_sumatra():
    import sumatra.programs
    import sumatra.recordstore.django_store.models
    import sumatra.versioncontrol.base
    sumatra.programs.Executable._find_executable = lambda self, name: name
    def repos_to_sumatra(self):
        cls = type(str(self.type), (sumatra.versioncontrol.base.Repository,), {})
        return cls(self.url)
    sumatra.recordstore.django_store.models.Repository.to_sumatra = repos_to_sumatra #patch for Michele Mattioni, who started using GitRepository early


def _get_class_path(obj):
    return obj.__class__.__module__ + "." + obj.__class__.__name__


def export_project(output_file):
    if minor_version == 3:
        shutil.copy(".smt/project", ".smt/project_export.json")
        return
    elif minor_version == 1:
        prj = projects.load_simulation_project()
    else:
        prj = projects.load_project()
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
        'description': getattr(prj, "description", ""), # not in 0.1
        'data_label': getattr(prj, "data_label", None), # not in 0.1
        '_most_recent': getattr(prj, "_most_recent", ""), # not in 0.1
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
    with open(output_file, 'w') as f:
        json.dump(state, f, indent=2)


if __name__ == "__main__":
    export_records(".smt/records_export.json")
    export_project(".smt/project_export.json")
