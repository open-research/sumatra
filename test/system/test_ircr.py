"""
A run through of basic Sumatra functionality.

As our example code, we will use a Python program for analyzing scanning
electron microscope (SEM) images of glass samples. This example was taken from
an online SciPy tutorial at http://scipy-lectures.github.com/intro/summary-exercises/image-processing.html

Usage:
    nosetests -v test_ircr.py
or:
    python test_ircr.py
"""
from __future__ import print_function
from __future__ import unicode_literals
from builtins import input

# Requirements: numpy, scipy, matplotlib, mercurial, sarge
import os
from datetime import datetime
import utils
from utils import (setup, teardown, run_test, build_command, assert_file_exists, assert_in_output,
                   assert_config, assert_label_equal, assert_records, edit_parameters,
                   expected_short_list, substitute_labels)

repository = "https://bitbucket.org/apdavison/ircr2013"
#repository = "/Volumes/USERS/andrew/dev/ircr2013"  # during development
#repository = "/Users/andrew/dev/ircr2013"


def modify_script(filename):
    def wrapped():
        with open(os.path.join(utils.working_dir, filename), 'rb') as fp:
            script = fp.readlines()
        with open(os.path.join(utils.working_dir, filename), 'wb') as fp:
            for line in script:
                if "print mean_bubble_size, median_bubble_size" in line:
                    fp.write('print "Mean:", mean_bubble_size\nprint "Median:", median_bubble_size\n')
                else:
                    fp.write(line)
    return wrapped


test_steps = [
    ("Get the example code",
     "hg clone %s ." % repository,
     assert_in_output, "updating to branch default"),
    ("Run the computation without Sumatra",
     "python glass_sem_analysis.py default_parameters MV_HFV_012.jpg",
     assert_in_output, "2416.86315789 60.0",
     assert_file_exists, os.path.join("Data", datetime.now().strftime("%Y%m%d")),  # Data subdirectory contains another subdirectory labelled with today's date)
     ),  # assert(subdirectory contains three image files).
    ("Set up a Sumatra project",
     "smt init -d Data -i . ProjectGlass",
     assert_in_output, "Sumatra project successfully set up"),
    ("Run the ``glass_sem_analysis.py`` script with Sumatra",
     "smt run -e python -m glass_sem_analysis.py -r 'initial run' default_parameters MV_HFV_012.jpg",
     assert_in_output, ("2416.86315789 60.0", "histogram.png")),
    ("Comment on the outcome",
     "smt comment 'works fine'"),
    ("Set defaults",
     "smt configure -e python -m glass_sem_analysis.py"),
    ("Look at the current configuration of the project",
     "smt info",
     assert_config, {"project_name": "ProjectGlass", "executable": "Python", "main": "glass_sem_analysis.py",
                     "code_change": "error"}),
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
    modify_script("glass_sem_analysis.py"),
    ("Run the modified code",
     "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg",
     assert_in_output, "Code has changed, please commit your changes"),
    ("Commit changes...",
     "hg commit -m 'Added labels to output'"),
    ("...then run again",
     "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg"),  # assert(output has changed as expected)
    #TODO: make another change to the Python script
    ("Change configuration to store diff",
     "smt configure --on-changed=store-diff"),
    ("Run with store diff",
     "smt run -r 'made a change' default_parameters MV_HFV_012.jpg"),  # assert(code runs, stores diff)
    ("Review previous computations - get a list of labels",
     "smt list",
     assert_in_output, expected_short_list),
    ("Review previous computations in detail",
     "smt list -l",
     assert_records, substitute_labels([
         {'label': 0, 'executable_name': 'Python', 'outcome': 'works fine', 'reason': 'initial run',
          'version': 'a98585eddfc7', 'vcs': 'Mercurial', 'script_args': '<parameters> MV_HFV_012.jpg',
          'main': 'glass_sem_analysis.py'},   # TODO: add checking of parameters
         {'label': 1, 'outcome': '', 'reason': 'No filtering'},
         {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
         {'label': 3, 'outcome': '', 'reason': 'Added labels to output'},
         {'label': 4, 'outcome': '', 'reason': 'made a change'},  # TODO: add checking of diff
     ])),
    ("Filter the output of ``smt list`` based on tag",
     "smt list mytag",
     #assert(list is correct)
    ),
    ("Export Sumatra records as JSON.",
     "smt export",
     assert_file_exists, ".smt/records_export.json"),
]


def test_all():
    """Test generator for Nose."""
    for step in test_steps:
        if callable(step):
            step()
        else:
            run_test.description = step[0]
            yield tuple([run_test] + list(step[1:]))

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
    response = eval(input("Do you want to delete the temporary directory (default: yes)? "))
    if response not in ["n", "N", "no", "No"]:
        teardown()
    else:
        print("Temporary directory %s not removed" % utils.temporary_dir)
