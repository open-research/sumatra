"""
Define URL dispatching for the Sumatra web interface.
"""

from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

urlpatterns = patterns('sumatra.web.views',
    (r'^$', 'list_projects'),
    (r'^(?P<project>\w+)/$', 'list_records'),
    (r'^(?P<project>\w+)/about/$', 'show_project'),
    (r'^(?P<project>\w+)/delete/$', 'delete_records'),
    (r'^(?P<project>\w+)/tag/$', 'list_tags'),
    (r'^(?P<project>\w+)/tag/(?P<tag>.*)/$', 'list_tagged_records'),
    (r'^(?P<project>\w+)/(?P<label>\w+[\w|\-\.]*)/$', 'record_detail'),
    (r'^(?P<project>\w+)/(?P<label>\w+[\w|\-\.]*)/datafile$', 'show_file'),
    (r'^(?P<project>\w+)/(?P<label>\w+[\w|\-\.]*)/download$', 'download_file'),
    (r'^(?P<project>\w+)/(?P<label>\w+[\w|\-\.]*)/image$', 'show_image'),
    (r'^(?P<project>\w+)/(?P<label>\w+[\w|\-\.]*)/diff/(?P<package>[\w_]+)*$', 'show_diff'),
)

urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
)