#!/usr/bin/env python

from distutils.core import setup
      
setup(
    name = "Sumatra",
    version = "0.1",
    package_dir={'sumatra': 'src'},
    packages = ['sumatra',],
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

