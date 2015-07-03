"""
Define URL dispatching for the Sumatra web interface.

:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""
from __future__ import unicode_literals

from django.conf.urls import patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from sumatra.projects import Project
from sumatra.records import Record
from sumatra.web.views import (ProjectListView, ProjectDetailView, RecordListView,
                               RecordDetailView, DataListView, DataDetailView,
                               SettingsView)

P = {
    'project': Project.valid_name_pattern,
    'label': Record.valid_name_pattern,
}

urlpatterns = patterns('',
                       (r'^$', ProjectListView.as_view()),
                       (r'^settings/$', SettingsView.as_view()),
                       (r'^%(project)s/$' % P, RecordListView.as_view()),
                       (r'^%(project)s/about/$' % P, ProjectDetailView.as_view()),
                       (r'^%(project)s/data/$' % P, DataListView.as_view()),
                       (r'^%(project)s/image$' % P, 'sumatra.web.views.image_list'),
                       (r'^%(project)s/delete/$' % P, 'sumatra.web.views.delete_records'),
                       (r'^%(project)s/compare/$' % P, 'sumatra.web.views.compare_records'),
                       (r'^%(project)s/%(label)s/$' % P, RecordDetailView.as_view()),
                       (r'^%(project)s/data/datafile$' % P, DataDetailView.as_view()),
                       (r'^data/(?P<datastore_id>\d+)$', 'sumatra.web.views.show_content'),
                       )

urlpatterns += staticfiles_urlpatterns()
