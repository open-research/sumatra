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

#repository = "https://bitbucket.org/apdavison/ircr2013"
repository = "/Volumes/USERS/andrew/dev/ircr2013"  # during development
#repository = "/Users/andrew/dev/ircr2013"

label_pattern = re.compile("Record label for this run: '(?P<label>\d{8}-\d{6})'")
label_pattern = re.compile("Record label for this run: '(?P<label>[\w\-_]+)'")

temporary_dir = os.path.realpath(tempfile.mkdtemp())
working_dir = os.path.join(temporary_dir, "sumatra_exercise")
os.mkdir(working_dir)
print working_dir
labels = []

def cleanup():
    if os.path.exists(temporary_dir):
        shutil.rmtree(temporary_dir)


def run(command):
    return sarge.run(command, cwd=working_dir, stdout=sarge.Capture())


def get_label(p):
    return label_pattern.search(p.stdout.text).groupdict()["label"]


# Get the example code
p = run("hg clone %s ." % repository)
assert "updating to branch default" in p.stdout.text
# TODO: update to the relevant version for the start of the project

# Run the computation without Sumatra::
p = run("python glass_sem_analysis.py default_parameters MV_HFV_012.jpg")
assert "2416.86315789 60.0" in p.stdout.text, p.stdout.text
#assert(Data subdirectory contains another subdirectory labelled with today's date)
#assert(subdirectory contains three image files).

# Set up a Sumatra project
p = run("smt init -d Data -i . ProjectGlass")
assert "Sumatra project successfully set up" in p.stdout.text, p.stdout.text

# Run the ``glass_sem_analysis.py`` script with Sumatra
p = run("smt run -e python -m glass_sem_analysis.py -r 'initial run' default_parameters MV_HFV_012.jpg")
assert "2416.86315789 60.0" in p.stdout.text
assert "Created Django record store using SQLite" in p.stdout.text
assert "histogram.png" in p.stdout.text
labels.append(get_label(p))
print "label0 is", labels[0]

# Comment on the outcome::
p = run("smt comment 'works fine'")

# Set defaults
p = run("smt configure -e python -m glass_sem_analysis.py")

# Look at the current configuration of the project
p = run("smt info")
expected_output = r"""Project name        : ProjectGlass
Default executable  : Python \(version: \d.\d.\d\) at /[\w\/]+/bin/python
Default repository  : MercurialRepository at \S+/sumatra_exercise \(upstream: \S+/ircr2013\)
Default main file   : glass_sem_analysis.py
Default launch mode : serial
Data store \(output\) : /[\w\/]+/sumatra_exercise/Data
.          \(input\)  : /[\w\/]+/sumatra_exercise
Record store        : Relational database record store using the Django ORM \(database file=/[\w\/]+/sumatra_exercise/.smt/records\)
Code change policy  : error
Append label to     : None
Label generator     : timestamp
Timestamp format    : %Y%m%d-%H%M%S
Sumatra version     : 0.6.0dev
"""
assert re.match(expected_output, p.stdout.text)

# Change some parameters
p = run("cp default_parameters no_filter")
# TODO change *filter_size* to 1.

p = run("smt run -l example_label -r 'No filtering' no_filter MV_HFV_012.jpg")
#assert(results have changed)
assert "phases.png" in p.stdout.text
labels.append(get_label(p))
print "label1 is", labels[1]
#assert label1 is "example_label"

# Change parameters from the command line
p = run("smt run -r 'Trying a different colourmap' default_parameters MV_HFV_012.jpg phases_colourmap=hot")
#assert(results have changed)
labels.append(get_label(p))

# Add another comment
p = run("smt comment 'The default colourmap is nicer'")
#TODO  add a comment to an older record (e.g. this colourmap is nicer than 'hot')

# Add tags on the command line::
p = run("smt tag mytag %s %s" % (labels[0], labels[1]))

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

# Run the modified code
p = run("smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg")
#assert("Code has changed, please commit your changes"
labels.append(get_label(p))

# Commit changes then run again
p = run("hg commit -m 'Added labels to output'")
p = run("smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg")
#assert(output has changed as expected)
labels.append(get_label(p))

#TODO: make another change to the Python script
# Run with store diff
p = run("smt configure --on-changed=store-diff")
p = run("smt run -r 'made a change' default_parameters MV_HFV_012.jpg")
#assert(code runs, stores diff)
labels.append(get_label(p))

# Review previous computations - get a list of labels
p = run("smt list")
assert p.stdout.text.strip() == "\n".join(reversed(labels)), "%s != %s" % (p.stdout.text, "\n".join(reversed(labels)))

# Review previous computations in detail
p = run("smt list -l")
#assert(information in p.stdout.text should match our expectations)

# Filter the output of ``smt list`` based on tag::
p = run("smt list mytag")
#assert(list is correct)


# Still to test:
#
#.. LaTeX example
#.. note that not only Python is supported - separate test
#.. play with labels? uuid, etc.
#.. move recordstore
#.. migrate datastore

response = raw_input("Do you want to delete the temporary directory? ")
if response in ["y", "Y", "yes"]:
    cleanup()
else:
    print "Temporary directory %s not removed" % temporary_dir
