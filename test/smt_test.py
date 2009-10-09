import tempfile
import os
import subprocess
import shutil
from sumatra.projects import load_simulation_project

def split(s):
    """
    Primitive way to split a command line string into arguments for Popen.
    I'm sure there's a nice, built-in way to do this, but it was quicker to
    write this than go searching.
    """
    parts = [""]
    in_str = False
    for c in s:
        if c == "'":
            if in_str:
                in_str = False
            else:
                in_str = True
        if in_str:
            parts[-1] += c
        else:
            if c == " ":
                parts.append("")
            else:
                parts[-1] += c
    return parts

def run(cmd):
    print
    print "="*60
    print cmd
    args = split(cmd)
    print args
    print "-"*60
    subprocess.check_call(args)

def create_mercurial_repos(repos_dir):
    run("hg init")
    run("hg add")
    run("hg commit -m 'Creating example project'")
    

def create_subversion_repos(repos_dir):
    run("svnadmin create %s" % repos_dir)
    run("svn checkout file://%s ." % repos_dir)
    file_list = os.listdir(".")
    file_list.remove(".svn")
    run("svn add %s" % " ".join(file_list))
    run("svn commit -m 'Creating example project'")

def copy_example_project(working_dir):
    for file in os.listdir("example_project"):
        shutil.copy("example_project/"+file, working_dir)

def get_last_simulation_id():
    project = load_simulation_project()
    return project._most_recent

def initialize_sumatra_project(plugins=None):
    if plugins:
        run("smt init TestProject --plugins=%s" % plugins)
    else:
        run("smt init TestProject")

def getting_started(plugins):
    initialize_sumatra_project(plugins)
        
    run("smt run --simulator=python --main=main.py default.param")
    id0 = get_last_simulation_id()
    run("smt list")
    run("smt list --long")
    run("smt configure --simulator=python --main=main.py")
    run("smt run default.param")
    run("smt info")
    run("smt run --label=haggling --reason='determine whether the gourd is worth 3 or 4 shekels' romans.param")
    id1 = get_last_simulation_id()
    run("smt comment 'apparently, it is worth NaN shekels.'")
    run("smt comment %s 'Eureka! Nobel prize here we come.'" % id0)
    run("smt tag foobar")
    run("smt tag barfoo")
    run("smt tag --remove barfoo")
    run("smt run --reason='test effect of a smaller time constant' default.param tau_m=10.0")
    run("smt repeat %s" % id1)
    run("smt delete %s" % id0)
    run("smt delete --group default")
    #run("smt delete --tag foobar")
    try:
        run("smt")
    except subprocess.CalledProcessError: # smt without any arguments returns a non-zero exit status
        pass
    run("smt comment --help")
    run("smt help list")
    run("smt list -l")

if __name__ == "__main__":
    cwd = os.getcwd()
    
    for repos in 'subversion',: #'subversion', 'mercurial':
        for plugins in ("sumatra.recordstore.shelve_store",  None):
            working_dir = tempfile.mkdtemp()
            repos_dir = tempfile.mkdtemp()
            print working_dir, repos_dir
    
            copy_example_project(working_dir)
            os.chdir(working_dir)
        
            exec("create_%s_repos('%s')" % (repos, repos_dir))
        
            getting_started(plugins)
        
            os.chdir(cwd)
            shutil.rmtree(working_dir)
            shutil.rmtree(repos_dir)
