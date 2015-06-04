"""


:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from __future__ import unicode_literals


import subprocess
import pkg_resources
from sumatra.dependency_finder import core

package_split_str = 'pkg::\n'
element_split_str = '\n'
name_value_split_str = ':'
r_script_to_find_deps = pkg_resources.resource_filename("sumatra", "external_scripts/script_introspect.R")



class Dependency(core.BaseDependency):
    """
    R dependency information.
    """
    module = 'r'

    def __init__(self, module_name, path=None, version='unknown', diff='', source=None):
        super(Dependency, self).__init__(module_name, path, version, diff, source)


def _get_r_dependencies(executable_path, rscriptfile, depfinder=r_script_to_find_deps,
                       pkg_split=package_split_str, el_split=element_split_str,
                       nv_split=name_value_split_str):
    """Return a string describing dependencies of an rscriptfile.

    Parameters
    ----------
    executable_path : path
        Rscript executable
    rscriptfile : path
        script file to be evaluated
    rscriptfile : depfinder
        R script that finds dependencies
    pkg_split : str
        delimit packages in output
    el_split : str
        delimit descriptive elements within packages in output
    nv_split : str
        delimit names from values within elements in output

    Returns
    -------
    str
        after each pkg_split several name-value pairs (separated by nv_split)
        separted by el_split

        This work is done in R by script contained
        in rintrospection variable in this module.

    Raises
    ------
    """
    parglist = [executable_path, depfinder,
                rscriptfile, pkg_split, el_split, nv_split]
    p = subprocess.Popen(parglist, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = p.wait()
    output = p.stdout.read()
    # import pdb; pdb.set_trace()
    return result, output

def _parse_deps(deps, pkg_split=package_split_str,
                el_split=element_split_str,
                nv_split=name_value_split_str):
    """Return list of dependencies.

    Parameters
    ----------
    deps : str
        String as produced by _get_r_dependencies

    Returns
    -------
    list
         lits contains Dependency for all packages imported by the R file
    """
    deps = deps.rstrip()
    pkgs = deps.split(pkg_split)[1:] ## first split may be a warning
    list_deps = []
    for pk in pkgs:
        parts = [x for x in pk.split(el_split) if len(x) > 0]
        argdict = {}
        for p in parts:
            k, v = p.split(nv_split)
            argdict[k.strip()] = v.strip()

        list_deps.append(Dependency(argdict.pop('name'), **argdict))
    return list_deps


def find_dependencies(filename, executable):
    """Return list of dependencies.

    First determines dependency info for filename. This is done through an external call
    (using the Rscript from exectuable.path) to a custom R script that uses parse
    and simple pattern-matching to find all calls in filename that load external
    packages (i.e., the R calls "library" and "require"). The result is returned
    in a string with package info delimited by pre-set tokens. Info includes:
    name, version, local path, and repo source (repo name but no URLs).

    Second, parses the dependency info into Dependency objects, returned in a list.
    """
    # filename : path
    #     R file to be evaluated for dependency
    # executable : ?
    #     Executable object with executable.path location of exectuable Rscript

    # Returns
    # -------
    # list
    #      lits contains Dependency object for all packages imported by the R file

    res, deps = _get_r_dependencies(executable.path, filename) #executable.path
    # if res != 0 handle errors
    return _parse_deps(deps)
