"""
A run through of basic Sumatra functionality.

As our example code, we will use a Python program for analyzing scanning
electron microscope (SEM) images of glass samples. This example was taken from
an online SciPy tutorial at http://scipy-lectures.github.com/intro/summary-exercises/image-processing.html
"""

# Requirements: numpy, scipy, matplotlib, mercurial, sarge
import os
import tempfile
import shutil
import re
import sarge

repository = "https://bitbucket.org/apdavison/ircr2013"
#repository = "/Volumes/USERS/andrew/dev/ircr2013"  # during development
#repository = "/Users/andrew/dev/ircr2013"

label_pattern = re.compile("Record label for this run: '(?P<label>\d{8}-\d{6})'")
label_pattern = re.compile("Record label for this run: '(?P<label>[\w\-_]+)'")

info_pattern = r"""Project name        : (?P<project_name>\w+)
Default executable  : (?P<executable>\w+) \(version: \d.\d.\d\) at /[\w\/]+/bin/python
Default repository  : MercurialRepository at \S+/sumatra_exercise \(upstream: \S+/ircr2013\)
Default main file   : (?P<main>\w+.\w+)
Default launch mode : serial
Data store \(output\) : /[\w\/]+/sumatra_exercise/Data
.          \(input\)  : /[\w\/]+/sumatra_exercise
Record store        : Relational database record store using the Django ORM \(database file=/[\w\/]+/sumatra_exercise/.smt/records\)
Code change policy  : (?P<code_change>\w+)
Append label to     : None
Label generator     : timestamp
Timestamp format    : %Y%m%d-%H%M%S
Sumatra version     : 0.6.0dev
"""


def setup():
    global temporary_dir, working_dir, labels
    temporary_dir = os.path.realpath(tempfile.mkdtemp())
    working_dir = os.path.join(temporary_dir, "sumatra_exercise")
    os.mkdir(working_dir)
    print working_dir
    labels = []


def teardown():
    if os.path.exists(temporary_dir):
        shutil.rmtree(temporary_dir)


def run(command):
    return sarge.run(command, cwd=working_dir, stdout=sarge.Capture())


def get_label(p):
    match = label_pattern.search(p.stdout.text)
    if match is not None:
        return match.groupdict()["label"]
    else:
        return None


def assert_in_output(p, texts):
    if isinstance(texts, basestring):
        texts = [texts]
    for text in texts:
        assert text in p.stdout.text, "'{}' is not in '{}'".format(text, p.stdout.text)


def assert_config(p, expected_config):
    match = re.match(info_pattern, p.stdout.text)
    assert match
    for key, value in expected_config.items():
        assert match.groupdict()[key] == value, "expected {} = {}, actually {}".format(key, value, match.groupdict()[key])


def expected_short_list(labels):
    return "\n".join(reversed(labels))


def build_command(template):
    def wrapped(args):
        return template.format(*args)
    return wrapped


def run_test(description, command, check=None, checkarg=None):
    global labels
    print description
    if callable(command):
        command = command(labels)
    p = run(command)
    if check:
        if callable(checkarg):
            checkarg = checkarg(labels)
        check(p, checkarg)
    label = get_label(p)
    if label is not None:
        labels.append(label)
        print "label is", label
run_test.__test__ = False  # nose should not treat this as a test


test_steps = [
    ("Get the example code",
     "hg clone %s ." % repository,
     assert_in_output, "updating to branch default"),  # TODO: update to the relevant version for the start of the project
    ("Run the computation without Sumatra",
     "python glass_sem_analysis.py default_parameters MV_HFV_012.jpg",
     assert_in_output, "2416.86315789 60.0"),  # TODO: #assert(Data subdirectory contains another subdirectory labelled with today's date)
                                                       #assert(subdirectory contains three image files).
    ("Set up a Sumatra project",
     "smt init -d Data -i . ProjectGlass",
     assert_in_output, "Sumatra project successfully set up"),
    ("Run the ``glass_sem_analysis.py`` script with Sumatra",
     "smt run -e python -m glass_sem_analysis.py -r 'initial run' default_parameters MV_HFV_012.jpg",
     assert_in_output, ("2416.86315789 60.0", "Created Django record store using SQLite", "histogram.png")),
    ("Comment on the outcome",
     "smt comment 'works fine'"),
    ("Set defaults",
     "smt configure -e python -m glass_sem_analysis.py"),
    ("Look at the current configuration of the project",
     "smt info",
     assert_config, {"project_name": "ProjectGlass", "executable": "Python", "main": "glass_sem_analysis.py",
                     "code_change": "error"}),
    ("Change some parameters",
     "cp default_parameters no_filter"),  # TODO change *filter_size* to 1.")
    ("Run with changed parameters and user-defined label",
     "smt run -l example_label -r 'No filtering' no_filter MV_HFV_012.jpg",  # TODO: #assert(results have changed) #assert label1 is "example_label"
     assert_in_output, "phases.png"),
    ("Change parameters from the command line",
     "smt run -r 'Trying a different colourmap' default_parameters MV_HFV_012.jpg phases_colourmap=hot"),  # assert(results have changed)
    ("Add another comment",
     "smt comment 'The default colourmap is nicer'"),  #TODO  add a comment to an older record (e.g. this colourmap is nicer than 'hot')")
    ("Add tags on the command line",
     build_command("smt tag mytag {0} {1}")),
    # Changing your code
    # TODO modify the code
    #The output printed by the ``glass_sem_analysis.py`` is not very useful. Let's add
    #some labels. Open the file in a text editor and replace::

    #    print mean_bubble_size, median_bubble_size
    #
    #with::
    #
    #    print "Mean:", mean_bubble_size
    #    print "Median:", median_bubble_size
    ("Run the modified code",
     "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg",
     #assert_in_output("Code has changed, please commit your changes"
     ),
    ("Commit changes...",
     "hg commit -m 'Added labels to output'"),
    ("...then run again",
     "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg"),  # assert(output has changed as expected)
    #TODO: make another change to the Python script
    ("Change configuration to store diff",
     "smt configure --on-changed=store-diff"),
    ("Run with store diff",
     "smt run -r 'made a change' default_parameters MV_HFV_012.jpg"),  #  #assert(code runs, stores diff)
    ("Review previous computations - get a list of labels",
     "smt list",
     assert_in_output, expected_short_list),
    ("Review previous computations in detail",
     "smt list -l",
     #assert(information in p.stdout.text should match our expectations)
    ),
    ("Filter the output of ``smt list`` based on tag",
     "smt list mytag",
     #assert(list is correct)
    ),
]


def test_all():
    for step in test_steps:
        yield run_test, step

# Still to test:
#
#.. LaTeX example
#.. note that not only Python is supported - separate test
#.. play with labels? uuid, etc.
#.. move recordstore
#.. migrate datastore


if __name__ == '__main__':
    setup()
    for testcase, args in test_all():
        testcase(*args)
    response = raw_input("Do you want to delete the temporary directory? ")
    if response in ["y", "Y", "yes"]:
        teardown()
    else:
        print "Temporary directory %s not removed" % temporary_dir
