"""
Defines view functions and forms for the Sumatra web interface.
"""
from django import forms
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render_to_response
from sumatra.recordstore.django_store import models
from sumatra.projects import load_project, init_websettings
import os

NbCol = 14 # default number of columns

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
    nbCols = 14 
    form = RecordForm()  
    project_loaded = load_project()
    sim_list = models.Record.objects.filter(project__id=project).order_by('-timestamp')
    try:
        web_settings = load_project().web_settings
    except AttributeError:
        project_loaded.web_settings = init_websettings()   
    for key, item in project_loaded.web_settings.iteritems():
        if item:
            project_loaded.web_settings[key] = item
    project_loaded.save()
    web_settings = load_project().web_settings
    nb_per_page = int(web_settings['nb_records_per_page'])
    paginator = Paginator(sim_list, nb_per_page)
    # get names of all files in the current directory:
    files = os.listdir(os.getcwd())
    page_list = paginator.page(1)
    if web_settings['table_HideColumns'] is not None:
        nbCols_actual = NbCol - len(web_settings['table_HideColumns'])
    else:
        nbCols_actual = 14
    head_width = '%s%s' %(90.0/nbCols_actual, '%')
    if (nbCols_actual > 10):
        label_width = '150px'
    else:
        label_width = head_width
    dic = {'project_name': project,
           'form': form,
           'settings':web_settings,
           'object_list':page_list.object_list,
           'page_list':page_list,
           'paginator':paginator,
           'width':{'head': head_width, 'label':label_width},
           'active':'List of records',
           'files': files,
           'path':project_loaded.default_executable.path}
    return render_to_response('record_list.html', dic)