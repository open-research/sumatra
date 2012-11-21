import re
from sumatra.dependency_finder import core

import os
from sumatra.programs import get_executable

class Dependency(core.BaseDependency):
    """
    Contains information about a Hoc file, and tries to determine version information.
    """
    module = 'make'
    
    def __init__(self, name, path=None, version='unknown', diff=''):
        self.name = os.path.basename(name) # or maybe should be path relative to main file?
        if path:
            self.path = path
        else:
            self.path = os.path.abspath(name)
        #if not os.path.exists(self.path):
        #    raise IOError("File %s does not exist." % self.path)
        self.diff = ''
        self.version = version
    def is_file(self):
        return os.path.exists(self.path)
    
    def find_sub_dependencies(self):
        from sumatra import dependency_finder
        dependencies = []
        if self.is_file():
            try:
                executable = get_executable(script_file=self.path)
            except:
                return []
            dependencies = dependency_finder.find_dependencies(self.path, executable)
            print executable, self.path, dependencies
        
        return dependencies
            
    
def strip(l):
    return l.strip()

def build_dependency_graph(makefile_path):
    depends = {}
    all_sources = []
    with file(makefile_path) as fid:
        for line in fid:
            # find every dependency line of the form "<item>: <dependencies>"
            m = re.match('([\w\.\s/]+)\s*:\s*(.*)',line)     
            if m:
                targets = m.group(1)
                dependency_list = m.group(2)
                for item in targets.split(' '):
                    if not item:
                        continue
                    item = item.strip()
                    all_sources.append(item)
                    
                    # store the dependency list into a dictionary for later
                    if dependency_list:
                        sources = map(strip,dependency_list.split())
                        val =  depends.setdefault(item, []) 
                        val += sources
                        all_sources += sources
    all_sources = set(all_sources)
    return {'edges': depends, 'nodes': all_sources}

def find_sources_without_deps(graph):
    sources = graph['nodes']
    deps = graph['edges']
    pure_sources = [src for src in sources if not src in deps]
    return pure_sources

def find_dependencies(filename, executable):
    dep_graph = build_dependency_graph(filename)
    sources = find_sources_without_deps(dep_graph)
    heuristics = [core.find_versions_from_versioncontrol,]
    dependencies = [Dependency(name) for name in sources]
    dependencies = [d for d in dependencies if d.is_file()]
    dependencies = core.find_versions(dependencies, heuristics)
    extra_dependencies = [d.find_sub_dependencies() for d in dependencies]
    for d in extra_dependencies:
        dependencies += d
    return dependencies
    
    