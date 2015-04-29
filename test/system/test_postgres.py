"""
Tests using a PostgreSQL-based record store.


Usage:
    nosetests -v test_postgres.py
or:
    python test_postgres.py
"""

import os
from urlparse import urlparse
try:
    import docker
    if "DOCKER_HOST" in os.environ:
        have_docker = True
    else:
        have_docker = False
except ImportError:
    have_docker = False
try:
    from unittest2 import SkipTest
except ImportError:
    from unittest import SkipTest
import utils
from utils import setup, teardown as default_teardown, run_test, build_command
try:
    import psycopg2
    have_psycopg2 = True
except ImportError:
    have_psycopg2 = False

ctr = None
dkr = None
image = "postgresql_test"


def create_script():
    with open(os.path.join(utils.working_dir, "main.py"), "w") as fp:
        fp.write("print('Hello world!')\n")


def get_url():
    info = dkr.containers()[0]
    assert info["Image"] == "{}:latest".format(image)
    host = urlparse(dkr.base_url).hostname
    return "{}:{}".format(host, info["Ports"][0]["PublicPort"])


def start_pg_container():
    """
    Launch a Docker container running PostgreSQL, return the URL.

    Requires the "postgresql_test" image. If this does not yet exist, run

        docker build -t postgresql_test - < fixtures/Dockerfile.postgres
    """
    global ctr, dkr
    env = docker.utils.kwargs_from_env(assert_hostname=False)
    dkr = docker.Client(timeout=60, **env)
    # docker run -rm -P -name pg_test postgresql_test
    ctr = dkr.create_container(image, command=None, hostname=None, user=None,
                               detach=False, stdin_open=False, tty=False, mem_limit=0,
                               ports=None, environment=None, dns=None, volumes=None,
                               volumes_from=None, network_disabled=False, name=None,
                               entrypoint=None, cpu_shares=None, working_dir=None)
    dkr.start(ctr, publish_all_ports=True)
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
    start_pg_container,
    ("Set up a Sumatra project",
     build_command("smt init --store=postgres://docker:docker@{}/sumatra_test -m main.py -e python MyProject", "url")),
     #"smt init -m main.py -e python MyProject"),
    ("Show project configuration", "smt info"),  # TODO: add assert
    ("Run a computation", "smt run")
]


# TODO: add test skips where docker, psycopg2 not found


def test_all():
    """Test generator for Nose."""
    if not have_psycopg2:
        raise SkipTest("Tests require psycopg2")
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
            print step[0]  # description
            run_test(*step[1:])
    response = raw_input("Do you want to delete the temporary directory (default: yes)? ")
    if response not in ["n", "N", "no", "No"]:
        teardown()
    else:
        print "Temporary directory %s not removed" % utils.temporary_dir
