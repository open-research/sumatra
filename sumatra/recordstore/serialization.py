"""
Handles serialization/deserialization of record store contents to/from JSON.


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from builtins import str

import json
from datetime import datetime
from sumatra import programs, launch, datastore, versioncontrol, parameters, dependency_finder
from sumatra.records import Record
from ..compatibility import string_type
from ..core import registry
from sumatra.formatting import record2json


def encode_record(record, indent=None):
    return record2json(record, indent)


def encode_project_info(long_name, description):
    """Encode a Sumatra project as JSON"""
    data = {}
    if long_name:
        data["name"] = long_name
    if description:
        data["description"] = description
    return json.dumps(data)


def keys2str(D):
    """
    Return a new dictionary whose keys are the same as in `D`, but converted
    to strings.
    """
    E = {}
    for k, v in list(D.items()):
        E[str(k)] = v
    return E


def decode_project_list(content):
    """docstring"""
    return json.loads(content)


def decode_project_data(content):
    """docstring"""
    return json.loads(content)
# shouldn't this be called decode_project_info, for symmetry?


def datestring_to_datetime(s):
    """docstring"""
    try:
        timestamp = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    return timestamp


def build_record(data):
    """Create a Sumatra record from a nested dictionary."""
    edata = data["executable"]
    cls = registry.components[programs.Executable].get(edata["name"], programs.Executable)
    executable = cls(edata["path"], edata["version"], edata.get("options", ""))
    executable.name = edata["name"]
    rdata = data["repository"]
    repos_cls = None
    for m in versioncontrol.vcs_list:
        if hasattr(m, rdata["type"]):
            repos_cls = getattr(m, rdata["type"])
            break
    if repos_cls is None:
        repos_cls = versioncontrol.base.Repository
    repository = repos_cls(rdata["url"])
    repository.upstream = rdata.get("upstream", None)
    pdata = data["parameters"]
    if pdata["type"] == "dict":
        parameter_set = eval(pdata["content"])
        assert isinstance(parameter_set, dict)
    else:
        parameter_set = getattr(parameters, pdata["type"])(pdata["content"])
    ldata = data["launch_mode"]
    lm_parameters = ldata["parameters"]
    if isinstance(lm_parameters, string_type):  # prior to 0.3
        lm_parameters = eval(lm_parameters)
    launch_mode = getattr(launch, ldata["type"])(**keys2str(lm_parameters))

    def build_data_store(ddata):
        ds_parameters = ddata["parameters"]
        if isinstance(ds_parameters, string_type):  # prior to 0.3
            ds_parameters = eval(ds_parameters)
        return getattr(datastore, ddata["type"])(**keys2str(ds_parameters))
    data_store = build_data_store(data["datastore"])
    if "input_datastore" in data:  # 0.4 onwards
        input_datastore = build_data_store(data["input_datastore"])
    else:
        input_datastore = datastore.FileSystemDataStore("/")
    input_data = data.get("input_data", [])
    if isinstance(input_data, string_type):  # 0.3
        input_data = eval(input_data)
    if input_data:
        if isinstance(input_data[0], string_type):  # versions prior to 0.4
            input_data = [datastore.DataKey(path, digest=datastore.IGNORE_DIGEST)
                          for path in input_data]
        else:
            input_data = [datastore.DataKey(keydata["path"], keydata["digest"], **keys2str(keydata["metadata"]))
                          for keydata in input_data]
    record = Record(executable, repository, data["main_file"],
                    data["version"], launch_mode, data_store, parameter_set,
                    input_data, data.get("script_arguments", ""),
                    data["label"], data["reason"], data["diff"],
                    data.get("user", ""), input_datastore=input_datastore,
                    timestamp=datestring_to_datetime(data["timestamp"]))
    tags = data["tags"]
    if not hasattr(tags, "__iter__"):
        tags = (tags,)
    record.tags = set(tags)
    record.output_data = []
    if "output_data" in data:
        for keydata in data["output_data"]:
            data_key = datastore.DataKey(keydata["path"], keydata["digest"], **keys2str(keydata["metadata"]))
            record.output_data.append(data_key)
    elif "data_key" in data:  # (versions prior to 0.4)
        for path in eval(data["data_key"]):
            data_key = datastore.DataKey(path, digest=datastore.IGNORE_DIGEST)
            record.output_data.append(data_key)
    record.duration = data["duration"]
    record.outcome = data["outcome"]
    record.stdout_stderr = data.get("stdout_stderr", "")
    record.platforms = [launch.PlatformInformation(**keys2str(pldata)) for pldata in data["platforms"]]
    record.dependencies = []
    for depdata in data["dependencies"]:
        dep_args = [depdata["name"], depdata["path"], depdata["version"],
                    depdata["diff"]]
        if "source" in depdata:  # 0.5 onwards
            dep_args.append(depdata["source"])
        dep = getattr(dependency_finder, depdata["module"]).Dependency(*dep_args)
        record.dependencies.append(dep)
    record.repeats = data.get("repeats", None)
    return record


def decode_record(content):
    """Create a Sumatra record from a JSON string."""
    return build_record(json.loads(content))


def decode_records(content):
    """Create multiple Sumatra records from a JSON string."""
    return [build_record(data) for data in json.loads(content)]
