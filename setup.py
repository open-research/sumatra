#!/usr/bin/env python


from setuptools import setup
from distutils.command.sdist import sdist
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
        repo = repository(ui(), path)
        tip = repo.changelog.tip()
        return str(repo.changelog.rev(tip))


setup(
    name = "Sumatra",
    version = "0.7dev",
    package_dir = {'sumatra': 'sumatra'},
    packages = ['sumatra', 'sumatra.dependency_finder', 'sumatra.datastore',
                'sumatra.recordstore', 'sumatra.recordstore.django_store',
                'sumatra.versioncontrol', 'sumatra.formatting',
                'sumatra.web', 'sumatra.web.templatetags',
                'sumatra.publishing',
                'sumatra.publishing.latex', 'sumatra.publishing.sphinxext'],
    package_data = {'sumatra': ['web/media/css/*.css', 'web/media/js/*.js',
                                'web/media/img/*', 'web/media/css/*.css', 'web/media/extras/fontawesome/font/*',
                                'web/media/extras/fontawesome/sass/*', 'web/media/extras/fontawesome/css/*.css',
                                'web/templates/*.html',
                                'publishing/latex/sumatra.sty',
                                'formatting/latex_template.tex']},
    scripts = ['bin/smt', 'bin/smtweb'],
    author = "Sumatra authors and contributors",
    author_email = "andrew.davison@unic.cnrs-gif.fr",
    description = "A tool for automated tracking of computation-based scientific projects",
    long_description = open('README').read(),
    license = "CeCILL http://www.cecill.info",
    keywords = "computational science simulation analysis project-management",
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
                        'docutils', 'jinja2', 'parameters'],
    extras_require = {'svn': 'pysvn',
                      'hg': 'mercurial',
                      'git': 'GitPython',
                      'bzr': 'bzr',
                      'mpi': 'mpi4py'}
)
