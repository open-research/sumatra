"""
Tests using a PostgreSQL-based record store.

"""

import os
import shutil
import tempfile
from urllib.parse import urlparse
try:
    import docker
    have_docker = True
except ImportError:
    have_docker = False
try:
    from fs.contrib.davfs import DAVFS
    have_davfs = True
except ImportError:
    have_davfs = False

from utils import run_test, build_command

import pytest

DOCKER_IMAGE = "webdav_test"


def get_url(ctr):
    ctr.reload()  # required to get auto-assigned ports
    info = ctr.ports["80/tcp"][0]
    return f"{info['HostIp']}:{info['HostPort']}"


@pytest.fixture(scope="module")
def server():
    """
    Launch a Docker container running apache/webdav, return the URL.

    Requires the "webdav_test" image. If this does not yet exist, run

        docker build -t webdav_test .

    in the fixtures subdir. Inputting the Dockerfile from stdin is not
    possible since we need to ADD an apache config file. See also:
    http://blog.mx17.net/2014/02/12/dockerfile-file-directory-error-using-add/
    """
    dkr = docker.from_env(timeout=60)
    ctr = dkr.containers.run(DOCKER_IMAGE, detach=True, publish_all_ports=True)
    container_url = get_url(ctr)
    yield container_url
    ctr.stop()


@pytest.mark.skipif(not have_docker, reason="Tests require docker Python package")
@pytest.mark.skipif(not have_davfs, reason="Tests require the fs.contrib.davfs package")
def test_all(server):
    """Run a series of Sumatra commands"""
    temporary_dir = os.path.realpath(tempfile.mkdtemp())
    working_dir = os.path.join(temporary_dir, "sumatra_exercise")
    os.mkdir(working_dir)
    env = {
        "labels": [],
        "working_dir": working_dir,
        "url": server
    }

    def create_script():
        with open(os.path.join(working_dir, "main.py"), "w") as fp:
            fp.write("print('Hello world!')\n")

    test_steps = [
        create_script,
        ("Create repository", "git init"),
        ("Add main file", "git add main.py"),
        ("Commit main file", "git commit -m 'initial'"),
        ("Set up a Sumatra project",
        build_command("smt init -W=http://sumatra:sumatra@{}/webdav/ -m main.py -e python MyProject", "url")),
        ("Show project configuration", "smt info"),  # TODO: add assert
        ("Run a computation", "smt run")
    ]

    for step in test_steps:
        if callable(step):
            step()
        else:
            run_test.description = step[0]
            run_test(*step[1:], env=env)

    shutil.rmtree(temporary_dir)
