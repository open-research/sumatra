import tempfile
import os
import subprocess
import shutil

cwd = os.getcwd()
working_dir = tempfile.mkdtemp()
repos_dir = tempfile.mkdtemp()
print working_dir, repos_dir

def run(cmd):
    quote_pos = cmd.find("'")
    if quote_pos == -1:
        args = cmd.split()
    else:
        args = cmd[:quote_pos].split()
        args.append(cmd[quote_pos:])
    subprocess.check_call(args)

def create_mercurial_repos():
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
    for file in "test.py", "defaults.param":
        shutil.copy("smtweb/"+file, working_dir)

def initialize_sumatra_project(plugins=None):
    if plugins:
        run("smt init TestProject --plugins=%s" % plugins)
    else:
        run("smt init TestProject")
    
copy_example_project(working_dir)
os.chdir(working_dir)

create_mercurial_repos()
#create_subversion_repos(repos_dir)

initialize_sumatra_project()
#initialize_sumatra_project("sumatra.recordstore.shelve_store")

os.chdir(cwd)
shutil.rmtree(working_dir)
shutil.rmtree(repos_dir)
