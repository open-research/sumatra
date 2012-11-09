"""
Handles serialization/deserialization of record store contents to/from JSON.
"""

try:
    import json
except ImportError:
    import simplejson as json
from datetime import datetime
from sumatra import programs, launch, datastore, versioncontrol, parameters, dependency_finder
from sumatra.records import Record


def encode_record(record, indent=None):
    data = {
        "label": record.label, # 0.1: 'group'
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": record.reason,
        "duration": record.duration,
        "executable": {
            "path": record.executable.path,
            "version": record.executable.version,
            "name": record.executable.name,
            "options": record.executable.options, # added in 0.3
         },
        "repository": {
            "url": record.repository.url,
            "type": record.repository.__class__.__name__,
            "upstream": record.repository.upstream,  # added in 0.5
        },
        "main_file": record.main_file,
        "version": record.version,
        "parameters": {
            "content": str(record.parameters),
            "type": record.parameters.__class__.__name__,
        },
        "input_data": [{  # changed in 0.4 (previously a list of strings)
            "path": key.path,
            "digest": key.digest,
            "metadata": key.metadata,
            } for key in record.input_data],
        "script_arguments": record.script_arguments, # added in 0.3
        "launch_mode": {
            "type": record.launch_mode.__class__.__name__, 
            "parameters": record.launch_mode.__getstate__(),
        },
        "datastore": {
            "type": record.datastore.__class__.__name__,
            "parameters": record.datastore.__getstate__(),
        },
        "input_datastore": { # added in 0.4
            "type": record.input_datastore.__class__.__name__,
            "parameters": record.input_datastore.__getstate__(),
        },
        "outcome": record.outcome or "",
        "stdout_stderr": record.stdout_stderr, # added in 0.4
        "output_data": [{  # added in 0.4 (replaced 'data_key', which was a string)
            "path": key.path,
            "digest": key.digest,
            "metadata": key.metadata,
            } for key in record.output_data],
        "tags": list(record.tags), # not sure if tags should be PUT, perhaps have separate URL for this?
        "diff": record.diff,
        "user": record.user, # added in 0.2
        "dependencies": [{
            "path": d.path,
            "version": d.version,
            "name": d.name,
            #"language": d.language,
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
    return json.dumps(data, indent=indent)


def encode_project_info(long_name, description):
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
    for k,v in D.items():
        E[str(k)] = v
    return E


def decode_project_list(content):
    return json.loads(content)


def decode_project_data(content):
    return json.loads(content)


def build_record(data):
    edata = data["executable"]
    cls = programs.registered_program_names.get(edata["name"], programs.Executable)
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
    if isinstance(lm_parameters, basestring): # prior to 0.3
        lm_parameters = eval(lm_parameters)
    launch_mode = getattr(launch, ldata["type"])(**keys2str(lm_parameters))
    def build_data_store(ddata):
        ds_parameters = ddata["parameters"]
        if isinstance(ds_parameters, basestring): # prior to 0.3
            ds_parameters = eval(ds_parameters)
        return getattr(datastore, ddata["type"])(**keys2str(ds_parameters))
    data_store = build_data_store(data["datastore"])
    if "input_data_store" in data: # 0.4 onwards
        input_datastore = build_data_store(data["input_data_store"])
    else:
        input_datastore = datastore.FileSystemDataStore("/")
    input_data = data.get("input_data", [])
    if isinstance(input_data, basestring): # 0.3
        input_data = eval(input_data)
    if input_data:
        if isinstance(input_data[0], basestring): # versions prior to 0.4
            input_data = [datastore.DataKey(path, digest=datastore.IGNORE_DIGEST)
                          for path in input_data]
        else:
            input_data = [datastore.DataKey(keydata["path"], keydata["digest"], **keys2str(keydata["metadata"]))
                          for keydata in input_data]
    record = Record(executable, repository, data["main_file"],
                       data["version"], launch_mode, data_store, parameter_set,
                       input_data, data.get("script_arguments", ""), 
                       data["label"], data["reason"], data["diff"],
                       data.get("user", ""), input_datastore=input_datastore)
    tags = data["tags"]
    if not hasattr(tags, "__iter__"):
        tags = (tags,)
    record.tags = set(tags)
    record.timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
    record.output_data = []
    if "output_data" in data:
        for keydata in data["output_data"]:
            data_key = datastore.DataKey(keydata["path"], keydata["digest"], **keys2str(keydata["metadata"]))
            record.output_data.append(data_key)
    elif "data_key" in data: # (versions prior to 0.4)
        for path in eval(data["data_key"]):
            data_key = datastore.DataKey(path, digest=datastore.IGNORE_DIGEST)
            record.output_data.append(data_key)
    record.duration = data["duration"]
    record.outcome = data["outcome"]
    record.stdout_stderr = data.get("stdout_stderr", "")
    record.platforms = [launch.PlatformInformation(**keys2str(pldata)) for pldata in data["platforms"]]
    record.dependencies = []
    for depdata in data["dependencies"]:
        dep = getattr(dependency_finder, depdata["module"]).Dependency(depdata["name"], depdata["path"], depdata["version"])
        dep.diff = depdata["diff"]
        record.dependencies.append(dep)
    return record


def decode_record(content):
    return build_record(json.loads(content))

    
def decode_records(content):
    return [build_record(data) for data in json.loads(content)]
