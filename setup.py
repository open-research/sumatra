#!/usr/bin/env python

from distutils.core import setup
from src.__init__ import __version__
      
setup(
    name = "Sumatra",
    version = __version__,
    package_dir={'sumatra': 'src'},
    packages = ['sumatra', 'sumatra.dependency_finder',
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
    long_description = """A tool for managing simulation-based projects.""",
    license = "CeCILL http://www.cecill.info",
    keywords = "computational neuroscience simulation project-management",
    url = "http://neuralensemble.org/Sumatra/",
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

