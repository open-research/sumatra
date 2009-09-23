from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

from sumatra.recordstore.django_store.models import SimulationRecord
from sumatra.projects import load_simulation_project

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

_project = load_simulation_project()
simulation_records = {
    "queryset": SimulationRecord.objects.all(),
    "template_name": "simulation_list.html",
    "extra_context": { 'project_name': _project.name }
}
del _project

urlpatterns = patterns('',
    # Example:
    (r'^$', list_detail.object_list, simulation_records),
    (r'^project/$', 'sumatra.web.views.show_project'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^delete/$', 'sumatra.web.views.delete_records'),
    (r'^(?P<id>\w+[\w\-\.]*)/$', 'sumatra.web.views.simulation_detail'),
    (r'^(?P<id>\w+[\w\-\.]*)/datafile$', 'sumatra.web.views.show_file'),
    (r'^(?P<id>\w+[\w\-\.]*)/image$', 'sumatra.web.views.show_image'),
    
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)