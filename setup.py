#!/usr/bin/env python

from distutils.core import setup
from src.__init__ import __version__
      
setup(
    name = "Sumatra",
    version = __version__,
    package_dir={'sumatra': 'src'},
    packages = ['sumatra', 'sumatra.dependency_finder',
                'sumatra.external',
                'sumatra.external.NeuroTools',
                'sumatra.recordstore', 'sumatra.recordstore.django_store',
                'sumatra.versioncontrol',
                'sumatra.web', 'sumatra.web.templatetags'],
    package_data = {'sumatra': ['web/media/smt.css',
                                'web/templates/*.html']},
    scripts= ['src/smt', 'src/smtweb'],
    author = "Andrew P. Davison",
    author_email = "andrewpdavison@gmail.com",
    description = "A tool for managing simulation-based projects",
    long_description = """Sumatra is a tool for managing and tracking projects based on numerical
simulation, with the aim of supporting reproducible research. It can be thought
of as an automated electronic lab notebook for simulation projects.

It consists of:

 * a command-line interface, smt, for launching simulations with automatic
   recording of information about the simulation, annotating these records,
   linking to data files, etc.
 * a web interface with a built-in web-server, smtweb, for browsing and
   annotating simulation results.
 * a Python API, on which smt and smtweb are based, that can be used in your own
   scripts in place of using smt, or could be integrated into a GUI-based
   application.

Sumatra is currently alpha code, and should be used with caution and frequent
backups of your simulation records.

For documentation, see http://neuralensemble.org/trac/sumatra/""",
    license = "CeCILL http://www.cecill.info",
    keywords = "computational neuroscience simulation project-management",
    url = "http://neuralensemble.org/trac/sumatra/",
    classifiers = ['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Environment :: Web Environment',
                   'Intended Audience :: Science/Research',
                   'License :: Other/Proprietary License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering'],
    requires = ['Django (>=1.1)'],
)

