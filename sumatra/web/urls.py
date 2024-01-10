"""
Define URL dispatching for the Sumatra web interface.

:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

from django.urls import re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from sumatra.projects import Project
from sumatra.records import Record
from sumatra.web.views import (
    ProjectListView,
    ProjectDetailView,
    RecordListView,
    RecordDetailView,
    DataListView,
    DataDetailView,
    ImageListView,
    SettingsView,
    DiffView,
    image_thumbgrid,
    parameter_list,
    delete_records,
    compare_records,
    show_script,
    datatable_record,
    datatable_data,
    datatable_image,
    show_content
)

P = {
    "project": Project.valid_name_pattern,
    "label": Record.valid_name_pattern,
}

urlpatterns = [
    re_path(r"^$", ProjectListView.as_view()),
    re_path(r"^settings/$", SettingsView.as_view()),
    re_path(r"^%(project)s/$" % P, RecordListView.as_view()),
    re_path(r"^%(project)s/about/$" % P, ProjectDetailView.as_view()),
    re_path(r"^%(project)s/data/$" % P, DataListView.as_view()),
    re_path(r"^%(project)s/image/$" % P, ImageListView.as_view()),
    re_path(r"^%(project)s/image/thumbgrid$" % P, image_thumbgrid),
    re_path(r"^%(project)s/parameter$" % P, parameter_list),
    re_path(r"^%(project)s/delete/$" % P, delete_records),
    re_path(r"^%(project)s/compare/$" % P, compare_records),
    re_path(r"^%(project)s/%(label)s/$" % P, RecordDetailView.as_view()),
    re_path(r"^%(project)s/%(label)s/diff$" % P, DiffView.as_view()),
    re_path(r"^%(project)s/%(label)s/diff/(?P<package>[\w_]+)*$" % P, DiffView.as_view()),
    re_path(r"^%(project)s/%(label)s/script$" % P, show_script),
    re_path(r"^%(project)s/data/datafile$" % P, DataDetailView.as_view()),
    re_path(r"^%(project)s/datatable/record$" % P, datatable_record),
    re_path(r"^%(project)s/datatable/data$" % P, datatable_data),
    re_path(r"^%(project)s/datatable/image$" % P, datatable_image),
    re_path(r"^data/(?P<datastore_id>\d+)$", show_content),
]

urlpatterns += staticfiles_urlpatterns()
