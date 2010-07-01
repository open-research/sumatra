"""
Define URL dispatching for the Sumatra web interface.
"""

from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

from sumatra.recordstore.django_store.models import Record
from sumatra.projects import load_project

from tagging.models import Tag

from copy import deepcopy

_project = load_project()
project_name = _project.name
del _project

records = {
    "queryset": Record.objects.filter(project=project_name),
    "template_name": "record_list.html",
    "extra_context": { 'project_name': project_name }
}

tagged_records = deepcopy(records)
tagged_records["queryset_or_model"] = Record
tagged_records.pop("queryset")

tags = {
    "extra_context": { 'project_name': project_name },
    "queryset": Tag.objects.all(),
    "template_name": "tag_list.html",
}

urlpatterns = patterns('',
    (r'^$', 'sumatra.web.views.list_records'),
    (r'^project/$', 'sumatra.web.views.show_project'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^delete/$', 'sumatra.web.views.delete_records'),
    (r'^tag/$', list_detail.object_list, tags),
    (r'^tag/(?P<tag>.*)/$', 'tagging.views.tagged_object_list', tagged_records),
    (r'^(?P<label>\w+[\w\-\.]*)/$', 'sumatra.web.views.record_detail'),
    (r'^(?P<label>\w+[\w\-\.]*)/datafile$', 'sumatra.web.views.show_file'),
    (r'^(?P<label>\w+[\w\-\.]*)/image$', 'sumatra.web.views.show_image'),
    (r'^(?P<label>\w+[\w\-\.]*)/diff/(?P<package>[\w_]+)*$', 'sumatra.web.views.show_diff'),
)