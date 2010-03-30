
import os
import tempfile
import subprocess
import shutil
import time
from pprint import pprint
from urlparse import urljoin

from smt_test import copy_example_project, create_mercurial_repos, getting_started

from twill.commands import go, formvalue, submit, follow, url, showlinks, info, back
from twill import get_browser

def run_in_background(cmd):
    return subprocess.Popen(cmd, shell=True)

def terminate(process):
    import signal  
    return os.kill(process.pid, signal.SIGTERM)

def visit_page(url, browser, results):
    go(url)
    results[url] = browser.get_code()
    for link in showlinks():
        full_url = urljoin(link.base_url, link.url) 
        if full_url not in results:
            visit_page(full_url, browser, results)
            browser.back()
    return results


def sort_by_code(results):
    sorted_results = {}
    for url, code in results.items():
        if code in sorted_results:
            sorted_results[code].append(url)
        else:
            sorted_results[code] = [url]
    return sorted_results

if __name__ == "__main__":
    cwd = os.getcwd()
    
    working_dir = os.path.realpath(tempfile.mkdtemp())
    copy_example_project(working_dir)
    os.chdir(working_dir)
    
    repos_dir = os.path.realpath(tempfile.mkdtemp())        
    create_mercurial_repos(repos_dir)
    
    getting_started(None)
        
    server = run_in_background("smtweb 8009")
    time.sleep(10)
    print "Server running"
    
    b = get_browser()
    results = {}
    results = visit_page("http://127.0.0.1:8009", b, results)
    pprint(sort_by_code(results))
    
    print "Project is in", working_dir
    print "Repository is in", repos_dir
    if hasattr(server, "terminate"): # Python >= 2.6
        server.terminate()
    else:
        terminate(server)
        
    os.chdir(cwd)
    shutil.rmtree(working_dir)
    shutil.rmtree(repos_dir)