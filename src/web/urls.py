from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

from sumatra.recordstore.django_store.models import SimulationRecord

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

simulation_records = {
    "queryset": SimulationRecord.objects.all(),
    "template_name": "simulation_list.html",
}

urlpatterns = patterns('',
    # Example:
    (r'^$', list_detail.object_list, simulation_records),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^(?P<id>\w+[\w\-\.]*)/$', 'sumatra.web.views.simulation_detail'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)