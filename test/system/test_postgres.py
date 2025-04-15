"""
Tests using a PostgreSQL-based record store.

"""

import os
from urllib.parse import urlparse
try:
    import docker
    have_docker = True
except ImportError:
    have_docker = False
import shutil
import tempfile
from utils import run_test, build_command
try:
    import psycopg2
    have_psycopg2 = True
except ImportError:
    have_psycopg2 = False

import pytest

DOCKER_IMAGE = "postgresql_test:15"


def get_url(ctr):
    ctr.reload()  # required to get auto-assigned ports
    info = ctr.ports["5432/tcp"][0]
    return f"{info['HostIp']}:{info['HostPort']}"


@pytest.fixture(scope="module")
def pg_container():
    """
    Launch a Docker container running PostgreSQL, return the URL.

    Requires the "postgresql_test" image. If this does not yet exist, run

        docker build -t postgresql_test - < fixtures/Dockerfile.postgres
    """
    dkr = docker.from_env()
    ctr = dkr.containers.run(DOCKER_IMAGE, detach=True, publish_all_ports=True)
    container_url = get_url(ctr)
    yield container_url
    ctr.stop()


@pytest.mark.skipif(not have_docker, reason="Tests require docker Python package")
@pytest.mark.skipif(not have_psycopg2, reason="Tests require psycopg2")
def test_all(pg_container):
    """Run a series of Sumatra commands"""
    temporary_dir = os.path.realpath(tempfile.mkdtemp())
    working_dir = os.path.join(temporary_dir, "sumatra_exercise")
    os.mkdir(working_dir)
    env = {
        "labels": [],
        "working_dir": working_dir,
        "url": pg_container
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
        build_command("smt init --store=postgres://docker:docker@{}/sumatra_test -m main.py -e python MyProject", "url")),
        #"smt init -m main.py -e python MyProject"),
        ("Show project configuration", "smt info"),  # TODO: add assert
        ("Run a computation", "smt run")
    ]
    for step in test_steps:
        if callable(step):
            step()
        else:
            run_test(*step[1:], env=env)

    shutil.rmtree(temporary_dir)
