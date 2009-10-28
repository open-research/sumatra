"""
Define URL dispatching for the Sumatra web interface.
"""

from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

from sumatra.recordstore.django_store.models import SimulationRecord
from sumatra.projects import load_simulation_project

from tagging.models import Tag

from copy import deepcopy

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

_project = load_simulation_project()
project_name = _project.name
del _project

simulation_records = {
    "queryset": SimulationRecord.objects.all(),
    "template_name": "simulation_list.html",
    "extra_context": { 'project_name': project_name }
}

tagged_records = deepcopy(simulation_records)
tagged_records["queryset_or_model"] = SimulationRecord
tagged_records.pop("queryset")

tags = {
    "extra_context": { 'project_name': project_name },
    "queryset": Tag.objects.all(),
    "template_name": "tag_list.html",
}

urlpatterns = patterns('',
    # Example:
    #(r'^$', list_detail.object_list, simulation_records),
    (r'^$', 'sumatra.web.views.list_simulations'),
    (r'^project/$', 'sumatra.web.views.show_project'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^delete/$', 'sumatra.web.views.delete_records'),
    (r'^tag/$', list_detail.object_list, tags),
    (r'^tag/(?P<tag>.*)/$', 'tagging.views.tagged_object_list', tagged_records),
    (r'^(?P<id>\w+[\w\-\.]*)/$', 'sumatra.web.views.simulation_detail'),
    (r'^(?P<id>\w+[\w\-\.]*)/datafile$', 'sumatra.web.views.show_file'),
    (r'^(?P<id>\w+[\w\-\.]*)/image$', 'sumatra.web.views.show_image'),
    (r'^(?P<id>\w+[\w\-\.]*)/diff/(?P<package>[\w_]+)*$', 'sumatra.web.views.show_diff'),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)