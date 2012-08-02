"""
Defines view functions and forms for the Sumatra web interface.
"""
from django import forms
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response
from sumatra.recordstore.django_store import models
from sumatra.projects import load_project, init_websettings
from services import initSettings, renderColWidth
import os

class SearchForm(forms.ModelForm):
    ''' this class will be inherited after. It is for changing the 
    requirement properties for any field in the search form'''
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        for key, field in self.fields.iteritems():
            self.fields[key].required = False
            
class RecordForm(SearchForm):
    executable = forms.ModelChoiceField(queryset=models.Executable.objects.all(), empty_label='')
    repository = forms.ModelChoiceField(queryset=models.Repository.objects.all(), empty_label='')
    timestamp = forms.DateTimeField(label="Date")

    class Meta:
        model = models.Record
        fields = ('label', 'tags', 'reason', 'executable', 'repository',
                  'main_file', 'script_arguments', 'timestamp')

def list_records(request, project):
    form = RecordForm() # search form  
    loaded_prj = load_project() # project object
    sim_list = models.Record.objects.filter(project__id=project).order_by('-timestamp') # project: string
    web_settings = initSettings(loaded_prj)
    nb_per_page = int(web_settings['nb_records_per_page'])
    paginator = Paginator(sim_list, nb_per_page)
    files = os.listdir(os.getcwd()) # names of all files and folders in current directory
    page_list = paginator.page(1) # always open the first page
    rendered_width = renderColWidth(web_settings)
    dic = {'project_name': project,
           'form': form,
           'settings':web_settings,
           'object_list':page_list.object_list,
           'page_list':page_list,
           'paginator':paginator,
           'width':rendered_width,
           'active':'List of records',
           'files': files,
           'path':loaded_prj.default_executable.path}
    return render_to_response('record_list.html', dic)