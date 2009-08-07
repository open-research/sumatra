from django.http import HttpResponse
from django.shortcuts import render_to_response
from sumatra.recordstore.django_store import models

def index(request):
    return HttpResponse("Welcome to the Sumatra web interface.")

def simulation_detail(request, id):
    record = models.SimulationRecord.objects.get(id=id)
    #SimulationUpdateForm = forms.form_for_instance(record, fields=('reason', 'outcome', 'tags'))
    
    #if request.method == 'POST':
    #    if request.POST.has_key('delete'):
    #        record.delete()
    #        return HttpResponseRedirect('/')
    #    else:
    #        form = SimulationUpdateForm(request.POST)
    #        if form.is_valid():
    #            form.save()
    #        return HttpResponseRedirect('/')
    #else:
    #    form = SimulationUpdateForm()
    
    #try:
    #    data_archive = tarfile.open(os.path.join(DATAROOT, record.id + ".tar.gz"),'r:gz')
    #    archive_contents = data_archive.getmembers()
    #    data_archive.close()
    #except IOError:
    #    archive_contents = []
    
    return render_to_response('simulation_detail.html', {'record': record,
                                                         #'parameters': record.iterparams(),
                                                         #'datafiles': archive_contents,
                                                         #'form': form
                                                         })