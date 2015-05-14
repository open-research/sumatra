"""
Tests using a PostgreSQL-based record store.


Usage:
    nosetests -v test_webdav.py
or:
    python test_webdav.py
"""
from __future__ import print_function

import os
from urlparse import urlparse
try:
    import docker
    have_docker = True
except ImportError:
    have_docker = False
try:
    from unittest2 import SkipTest
except ImportError:
    from unittest import SkipTest
import utils
from utils import setup, teardown as default_teardown, run_test, build_command

ctr = None
dkr = None
IMAGE = "webdav_test"


def create_script():
    with open(os.path.join(utils.working_dir, "main.py"), "w") as fp:
        fp.write("print('Hello world!')\n")


def get_url():
    info = dkr.containers()[0]
    assert info["Image"] == "{}:latest".format(IMAGE)
    host = urlparse(dkr.base_url).hostname
    return "{}:{}".format(host, info["Ports"][0]["PublicPort"])


def start_webdav_container():
    """
    Launch a Docker container running apache/webdav, return the URL.

    Requires the "webdav_test" image. If this does not yet exist, run

        docker build -t webdav_test .

    in the fixtures subdir. Inputting the Dockerfile from stdin is not 
    possible since we need to ADD an apache config file. See also:
    http://blog.mx17.net/2014/02/12/dockerfile-file-directory-error-using-add/
    """
    global ctr, dkr
    env = docker.utils.kwargs_from_env(assert_hostname=False)
    dkr = docker.Client(timeout=60, **env)
    ctr = dkr.create_container(IMAGE, command=None, hostname=None, user=None,
                               detach=False, stdin_open=False, tty=False, mem_limit=0,
                               ports=[80], environment=None, dns=None, volumes=None,
                               volumes_from=None, network_disabled=False, name=None,
                               entrypoint=None, cpu_shares=None, working_dir=None)
    dkr.start(ctr, port_bindings={80: 8080})
    print(get_url())
    utils.env["url"] = get_url()


def teardown():
    global ctr, dkr
    default_teardown()
    if dkr is not None:
        dkr.stop(ctr)


test_steps = [
    create_script,
    ("Create repository", "git init"),
    ("Add main file", "git add main.py"),
    ("Commit main file", "git commit -m 'initial'"),
    start_webdav_container,
    ("Set up a Sumatra project",
     build_command("smt init -W=http://sumatra:sumatra@{}/webdav/ -m main.py -e python MyProject", "url")),
     #"smt init -m main.py -e python MyProject"),
    ("Show project configuration", "smt info"),  # TODO: add assert
    ("Run a computation", "smt run")
]


def test_all():
    """Test generator for Nose."""
    if not have_docker:
        raise SkipTest("Tests require docker")
    for step in test_steps:
        if callable(step):
            step()
        else:
            run_test.description = step[0]
            yield tuple([run_test] + list(step[1:]))


if __name__ == '__main__':
    # Run the tests without using Nose.
    setup()
    for step in test_steps:
        if callable(step):
            step()
        else:
            print(step[0])  # description
            run_test(*step[1:])
    response = raw_input("Do you want to delete the temporary directory (default: yes)? ")
    if response not in ["n", "N", "no", "No"]:
        teardown()
    else:
        print("Temporary directory %s not removed" % utils.temporary_dir)
