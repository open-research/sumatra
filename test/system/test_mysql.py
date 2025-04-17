"""
Tests using a MariaDB/MySQL-based record store.

"""

import os
import shutil
import tempfile
from time import sleep

try:
    import docker
    have_docker = True
except ImportError:
    try:
        import podman
        docker = podman.PodmanClient
        have_docker = True
    except ImportError:
        have_docker = False

try:
    import MySQLdb
    have_mysql = True
except ImportError:
    have_mysql = False


from utils import run_test, build_command

import pytest

DOCKER_IMAGE = "docker.io/mariadb:latest"


def get_url(ctr):
    ctr.reload()  # required to get auto-assigned ports
    info = ctr.ports["3306/tcp"][0]
    return f"{info['HostIp'] or '127.0.0.1'}:{info['HostPort']}"


@pytest.fixture(scope="module")
def mysql_container():
    """
    Launch a Docker container running MariaDB, return the URL.

    """
    dkr = docker.from_env()
    ctr = dkr.containers.run(
        DOCKER_IMAGE, detach=True, publish_all_ports=True,
        environment={
            "MARIADB_ROOT_PASSWORD": "the_root_password",
            "MARIADB_DATABASE": "sumatra_test",
            "MARIADB_USER": "docker",
            "MARIADB_PASSWORD": "docker"
        }
    )
    container_url = get_url(ctr)
    sleep(15)  # time for the container to start properly
    yield container_url
    ctr.stop()
    if hasattr(dkr, "stop"):
        dkr.stop()


@pytest.mark.skipif(not have_docker, reason="Tests require docker Python package")
@pytest.mark.skipif(not have_mysql, reason="Tests require mysqlclient")
def test_all(mysql_container):
    """Run a series of Sumatra commands"""
    temporary_dir = os.path.realpath(tempfile.mkdtemp())
    working_dir = os.path.join(temporary_dir, "sumatra_exercise")
    os.mkdir(working_dir)
    env = {
        "labels": [],
        "working_dir": working_dir,
        "url": mysql_container
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
        build_command("smt init --store=mysql://docker:docker@{}/sumatra_test -m main.py -e python MyProject", "url")),
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
