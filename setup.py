#!/usr/bin/env python

import distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup
from distutils.command.sdist import sdist
from src.__init__ import __version__
import os


class sdist_hg(sdist):
    """Add revision number to version for development releases."""

    def run(self):
        if "dev" in self.distribution.metadata.version:
            self.distribution.metadata.version += self.get_tip_revision()
        sdist.run(self)

    def get_tip_revision(self, path=os.getcwd()):
        from mercurial.hg import repository
        from mercurial.ui import ui
        from mercurial import node
        repo = repository(ui(), path)
        tip = repo.changelog.tip()
        return str(repo.changelog.rev(tip))


setup(
    name = "Sumatra",
    version = __version__,
    package_dir = {'sumatra': 'src'},
    packages = ['sumatra', 'sumatra.dependency_finder',
                'sumatra.external', 'sumatra.datastore',
                'sumatra.external.NeuroTools',
                'sumatra.recordstore', 'sumatra.recordstore.django_store',
                'sumatra.versioncontrol',
                'sumatra.web', 'sumatra.web.templatetags',
                'sumatra.publishing',
                'sumatra.publishing.latex', 'sumatra.publishing.sphinxext'],
    package_data = {'sumatra': ['web/media/css/*.css', 'web/media/js/*.js',
                                'web/media/img/*', 'web/media/css/*.css', 'web/media/extras/fontawesome/font/*',
                                'web/media/extras/fontawesome/sass/*', 'web/media/extras/fontawesome/css/*.css',          
                                'web/templates/*.html',
                                'publishing/latex/sumatra.sty']},
    scripts = ['bin/smt', 'bin/smtweb'],
    author = "Andrew P. Davison",
    author_email = "andrewpdavison@gmail.com",
    description = "A tool for automated tracking of computation-based scientific projects",
    long_description = open('README').read(),
    license = "CeCILL http://www.cecill.info",
    keywords = "computational science neuroscience simulation analysis project-management",
    url = "http://neuralensemble.org/sumatra/",
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Environment :: Web Environment',
                   'Intended Audience :: Science/Research',
                   'License :: Other/Proprietary License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Scientific/Engineering'],
    cmdclass = {'sdist': sdist_hg},
    install_requires = ['Django>=1.4', 'django-tagging', 'httplib2',
                        'simplejson', 'docutils'],
    extras_require = {'svn': 'pysvn',
                      'hg': 'mercurial',
                      'git': 'GitPython',
                      'bzr': 'bzr',
                      'mpi': 'mpi4py'},
    tests_require = ['twill'],
)
