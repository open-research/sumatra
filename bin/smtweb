#!/usr/bin/env python
"""
Web interface to the Sumatra computational experiment management tool.
"""

import sys
import os
try:
    import thread
except ImportError: # Python 3. TODO: move to higher level ``threading`` module
    import _thread as thread
import webbrowser
from django.core import management
from django.conf import settings
from sumatra.projects import load_project
from sumatra.recordstore.django_store import DjangoRecordStore, db_config
from sumatra.web import __file__ as sumatra_web
from optparse import OptionParser
from textwrap import dedent
import time


def delayed_new_tab(url, delay):
    """
    Open a new browser tab with a time delay, to give the server enough
    time to start up.
    """

    time.sleep(delay)
    # maybe optional with python setup develop ?
    webbrowser.open_new_tab(url)


def main(argv):
    """Launch the Sumatra web interface"""
    usage = "%prog [options] [PATH]"
    description = dedent("""\
        Launch the Sumatra web interface. If PATH is provided, it is taken as
        the location of the record store. Otherwise, there must be a Sumatra
        project in the working directory and the record store for that project
        will be used.""")
    parser = OptionParser(usage=usage,
                          description=description)
    parser.add_option('-a', '--allips', default=False, action="store_true",
                      help="run server on all IPs, not just localhost")
    parser.add_option('-p', '--port', metavar='PORT', default="8000",
                      help="run server on this port number PORT")
    parser.add_option('-n', '--no-browser', default=False, action="store_true",
                      help="do not open browser")
    parser.add_option('-r', '--read_only', default=False, action="store_true",
                      help="set read-only mode")
    parser.add_option('-s', '--serverside', default=False, action="store_true",
                      help="load website faster, recommended for large dataset")
    (options, args) = parser.parse_args(argv)

    if args:
        recordstore = DjangoRecordStore(db_file=args[0])
    else:
        project = load_project()
        if not isinstance(project.record_store, DjangoRecordStore):
            # should make the web interface independent of the record store, if possible
            print("This project cannot be accessed using the web interface (record store is not of type DjangoRecordStore).")
            sys.exit(1)
        del project

    root_dir = os.path.dirname(sumatra_web)
    db_config.update_settings(
        INSTALLED_APPS=db_config._settings["INSTALLED_APPS"] + ['sumatra.web'],
        ROOT_URLCONF='sumatra.web.urls',
        STATIC_URL='/static/',
        TEMPLATE_DIRS=(os.path.join(os.getcwd(), ".smt", "templates"),
                       os.path.join(root_dir, "templates"),),
        MIDDLEWARE_CLASSES=tuple(),
        READ_ONLY = options.read_only,
        SERVERSIDE = options.serverside,
    )

    db_config.configure()

    if not options.no_browser:
        thread.start_new_thread(delayed_new_tab, ("http://127.0.0.1:%s" % options.port, 3))

    if options.allips:
        address = '0.0.0.0'
    else:
        address = '127.0.0.1'
    address += ':' + options.port
    management.call_command('runserver', address, use_reloader=False)


if __name__ == "__main__":
    main(sys.argv[1:])
