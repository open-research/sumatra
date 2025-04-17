"""
Tests of the HttpRecordStore

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
    import httplib2
    have_httplib = True
except ImportError:
    have_httplib = False

from utils import (run_test, build_command, assert_in_output,
                   assert_label_equal, assert_records, edit_parameters,
                   expected_short_list, substitute_labels)

import pytest

repository = "https://github.com/apdavison/ircr2013"
DOCKER_IMAGE = "docker.io/apdavison/sumatra-server-v4"


def get_url(ctr):
    ctr.reload()  # required to get auto-assigned ports
    info = ctr.ports["80/tcp"][0]
    return f"{info['HostIp'] or 'localhost'}:{info['HostPort']}"


@pytest.fixture(scope="module")
def server():
    """
    Launch a Docker container running Sumatra Server, return the URL.

    Requires the "apdavison/sumatra-server-v4" DOCKER_IMAGE from the Docker Index.
    """
    dkr = docker.from_env(timeout=60)
    ctr = dkr.containers.run(DOCKER_IMAGE, detach=True, publish_all_ports=True)
    container_url = get_url(ctr)
    sleep(5)  # time for the all the processes in the container to start properly
    yield container_url
    ctr.stop()
    if hasattr(dkr, "stop"):
        dkr.stop()


@pytest.mark.skipif(not have_httplib, reason="This test requires httplib2")
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

    test_steps = [
        ("Get the example code",
        "git clone --progress %s ." % repository,
        assert_in_output, "done."),
        ("Set up a Sumatra project",
        build_command("smt init --store=http://testuser:abc123@{}/records/ -m glass_sem_analysis.py -e python -d Data -i . ProjectGlass", "url")),
        ("Run the ``glass_sem_analysis.py`` script with Sumatra",
        "smt run -r 'initial run' default_parameters MV_HFV_012.jpg",
        assert_in_output, ("2416.86315789", "histogram.png")),
        ("Comment on the outcome",
        "smt comment 'works fine'"),
        edit_parameters("default_parameters", "no_filter", "filter_size", 1, working_dir),
        ("Run with changed parameters and user-defined label",
        "smt run -l example_label -r 'No filtering' no_filter MV_HFV_012.jpg",  # TODO: assert(results have changed)
        assert_in_output, "phases.png",
        assert_label_equal, "example_label"),
        ("Change parameters from the command line",
        "smt run -r 'Trying a different colourmap' default_parameters MV_HFV_012.jpg phases_colourmap=hot"),  # assert(results have changed)
        ("Add another comment",
        "smt comment 'The default colourmap is nicer'"),  #TODO  add a comment to an older record (e.g. this colourmap is nicer than 'hot')")
        ("Add tags on the command line",
        build_command("smt tag mytag {0} {1}", "labels")),
        ("Review previous computations - get a list of labels",
        "smt list",
        assert_in_output, expected_short_list),
        ("Review previous computations in detail",
        "smt list -l",
        assert_records, substitute_labels([
            {'label': 0, 'executable_name': 'Python', 'outcome': 'works fine', 'reason': 'initial run',
            'version': 'e74b39374b0a1a401848b05ba9c86042aac4d8e4', 'vcs': 'Git', 'script_arguments': '<parameters> MV_HFV_012.jpg',
            'main_file': 'glass_sem_analysis.py'},   # TODO: add checking of parameters
            {'label': 1, 'outcome': '', 'reason': 'No filtering'},
            {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
        ])),
        # ("Filter the output of ``smt list`` based on tag",
        #  "smt list mytag",
        #  #assert(list is correct)
        # ),
        # ("Export Sumatra records as JSON.",
        #  "smt export",
        #  assert_file_exists, ".smt/records_export.json"),
        # ("Change to a local record store",
        #  "smt configure --store=sumatra.sqlite"),
        # ("Check the list of labels is unchanged",
        #  "smt list",
        #  assert_in_output, expected_short_list),
        # ("Run another computation, which will only be captured by the local record store",
        #  "smt repeat --label=repeated_example example_label"),
        # ("Switch back to the remote record store",
        #  build_command("smt configure --store=http://testuser:abc123@{}/records/", "url")),
        # ("Check that all records are listed",
        #  "smt list -l",
        #  assert_records, substitute_labels([
        #      {'label': 0, 'executable_name': 'Python', 'outcome': 'works fine', 'reason': 'initial run',
        #       'version': 'e74b39374b0a1a401848b05ba9c86042aac4d8e4', 'vcs': 'Git', 'script_args': '<parameters> MV_HFV_012.jpg',
        #       'main': 'glass_sem_analysis.py'},   # TODO: add checking of parameters
        #      {'label': 1, 'outcome': '', 'reason': 'No filtering'},
        #      {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
        #      {'label': 3, 'outcome': 'The new record exactly matches the original.'},
        #  ])),
    ]

    for step in test_steps:
        if callable(step):
            step()
        else:
            run_test(*step[1:], env=env)

    shutil.rmtree(temporary_dir)


# Still to test:
#
#.. LaTeX example
#.. note that not only Python is supported - separate test
#.. play with labels? uuid, etc.
#.. move recordstore
#.. migrate datastore
#.. repeats
#.. moving forwards and backwards in history
#.. upgrades (needs Docker)
