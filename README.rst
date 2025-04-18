=============
About Sumatra
=============

Sumatra is a tool for managing and tracking projects based on numerical
simulation and/or analysis, with the aim of supporting reproducible research.
It can be thought of as an automated electronic lab notebook for computational
projects.

It consists of:

* a command-line interface, smt, for launching simulations/analyses with
  automatic recording of information about the experiment, annotating these
  records, linking to data files, etc.
* a web interface with a built-in web-server, smtweb, for browsing and
  annotating simulation/analysis results.
* a Python API, on which smt and smtweb are based, that can be used in your own
  scripts in place of using smt, or could be integrated into a GUI-based
  application.

Sumatra is currently beta code, and should be used with caution and frequent
backups of your records.

For documentation, see http://neuralensemble.org/sumatra/


Functionality:

* launch simulations and analyses, and record various pieces of information,
  including:

  - the executable (identity, version)
  - the script (identity, version)
  - the parameters
  - the duration (execution time)
  - console output
  - links to all data (whether in files, in a database, etc.) produced by
    the simulation/analysis
  - the reason for doing the simulation/analysis
  - the outcome of the simulation/analysis

* allow browsing/searching/visualising the results of previous experiments
* allow the re-running of previous simulations/analyses with automatic
  verification that the results are unchanged
* launch single or batch experiments, serial or parallel


============
Requirements
============

Sumatra requires Python version 3.9 or later The web interface requires
Django (>= 4.2) and the django-tagging package.
Sumatra requires that you keep your own code in a version control
system (currently Subversion, Mercurial, Git and Bazaar are supported). If you
are already using Bazaar there is nothing else to install. If you
are using Subversion you will need to install the pysvn package. If you are using
Git, you will need to install git-python bindings, and for Mercurial install hg-api.


============
Installation
============

These instructions are for Unix and Mac OS. They may work on Windows as well, but
it hasn't been thoroughly tested.

The easiest way to install is with pip::

    $ pip install sumatra[default]

The "default" option installs the most commonly-used features:

- Git support
- the local web-based GUI
- support for remote record stores

Other options are available. For example, to install support for Mercurial and for using a
PostgreSQL database as the record store, run::

    $ pip install sumatra[default,hg,postgres]


===========
Code status
===========

.. image:: https://github.com/open-research/sumatra/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/open-research/sumatra/actions/workflows/tests.yml
   :alt: Unit Test Status

.. image:: https://coveralls.io/repos/open-research/sumatra/badge.svg
   :target: https://coveralls.io/repos/open-research/r/sumatra
   :alt: Code coverage
