"""
Define URL dispatching for the Sumatra web interface.
"""

from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

P = {
    'project': r'(?P<project>\w+[\w ]*)',
    'label': r'(?P<label>\w+[\w|\-\.]*)',
}

urlpatterns = patterns('sumatra.web.views',
    (r'^$', 'list_projects'),
    (r'^%(project)s/$' % P, 'list_records'),
    (r'^%(project)s/about/$' % P, 'show_project'),
    (r'^%(project)s/delete/$' % P, 'delete_records'),
    (r'^%(project)s/tag/$' % P, 'list_tags'),
    (r'^%(project)s/tag/(?P<tag>.*)/$' % P, 'list_tagged_records'),
    (r'^%(project)s/%(label)s/$' % P, 'record_detail'),
    (r'^%(project)s/%(label)s/datafile$' % P, 'show_file'),
    (r'^%(project)s/%(label)s/download$' % P, 'download_file'),
    (r'^%(project)s/%(label)s/image$' % P, 'show_image'),
    (r'^%(project)s/%(label)s/diff/(?P<package>[\w_]+)*$' % P, 'show_diff'),
)

urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
)