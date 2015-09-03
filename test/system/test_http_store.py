"""
Tests of the HttpRecordStore

Usage:
    nosetests -v test_http_store.py
or:
    python test_http_store.py
"""

from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
from builtins import input
standard_library.install_aliases()

import os
from urllib.parse import urlparse
from time import sleep

try:
    import docker
    if "DOCKER_HOST" in os.environ:
        have_docker = True
    else:
        have_docker = False
except ImportError:
    have_docker = False

import utils
from utils import (setup, teardown as default_teardown, run_test, build_command, assert_file_exists, assert_in_output,
                   assert_config, assert_label_equal, assert_records, edit_parameters,
                   expected_short_list, substitute_labels)
from functools import partial

#repository = "https://bitbucket.org/apdavison/ircr2013"
repository = "/Users/andrew/dev/ircr2013"
image = "apdavison/sumatra-server-v4"

ctr = None
dkr = None


def get_url():
    info = dkr.containers()[0]
    assert info["Image"] == "{0}:latest".format(image)
    host = urlparse(dkr.base_url).hostname
    return "{0}:{1}".format(host, info["Ports"][0]["PublicPort"])


def start_server():
    """
    Launch a Docker container running Sumatra Server, return the URL.

    Requires the "apdavison/sumatra-server-v4" image from the Docker Index.
    """
    global ctr, dkr
    env = docker.utils.kwargs_from_env(assert_hostname=False)
    dkr = docker.Client(timeout=60, **env)
    # docker run --rm -P --name smtserve apdavison/sumatra-server-v4
    ctr = dkr.create_container(image, command=None, hostname=None, user=None,
                               detach=False, stdin_open=False, tty=False, mem_limit=0,
                               ports=None, environment=None, dns=None, volumes=None,
                               volumes_from=None, network_disabled=False, name=None,
                               entrypoint=None, cpu_shares=None, working_dir=None)
    dkr.start(ctr, publish_all_ports=True)
    utils.env["url"] = get_url()
    sleep(5)  # give the server enough time to start


def teardown():
    global ctr, dkr
    default_teardown()
    if dkr is not None:
        dkr.stop(ctr)

##utils.env["url"] = "127.0.0.1:8642"


test_steps = [
    start_server,
    ("Get the example code",
     "hg clone %s ." % repository,
     assert_in_output, "updating to branch default"),
    ("Set up a Sumatra project",
     build_command("smt init --store=http://testuser:abc123@{}/records/ -m glass_sem_analysis.py -e python -d Data -i . ProjectGlass", "url")),
    ("Run the ``glass_sem_analysis.py`` script with Sumatra",
     "smt run -r 'initial run' default_parameters MV_HFV_012.jpg",
     assert_in_output, ("2416.86315789 60.0", "histogram.png")),
    ("Comment on the outcome",
     "smt comment 'works fine'"),
    edit_parameters("default_parameters", "no_filter", "filter_size", 1),
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
          'version': '6038f9c500d1', 'vcs': 'Mercurial', 'script_arguments': '<parameters> MV_HFV_012.jpg',
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
    #       'version': '6038f9c500d1', 'vcs': 'Mercurial', 'script_args': '<parameters> MV_HFV_012.jpg',
    #       'main': 'glass_sem_analysis.py'},   # TODO: add checking of parameters
    #      {'label': 1, 'outcome': '', 'reason': 'No filtering'},
    #      {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
    #      {'label': 3, 'outcome': 'The new record exactly matches the original.'},
    #  ])),
]


def test_all():
    """Test generator for Nose."""
    for step in test_steps:
        if callable(step):
            step()
        else:
            test = partial(*tuple([run_test] + list(step[1:])))
            test.description = step[0]
            yield test

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


if __name__ == '__main__':
    # Run the tests without using Nose.
    setup()
    for step in test_steps:
        if callable(step):
            step()
        else:
            print(step[0])  # description
            run_test(*step[1:])
    response = input("Do you want to delete the temporary directory (default: yes)? ")
    if response not in ["n", "N", "no", "No"]:
        teardown()
    else:
        print("Temporary directory %s not removed" % utils.temporary_dir)
