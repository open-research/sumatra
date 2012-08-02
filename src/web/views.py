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

def initSettings(project, option='web'):
    '''Checking existence of the specific settings in .smt/project.
    In case it doesn't exist, it will be initialized with some default values
    Inputs:
        project: project object,
        option: string.
    Output:
        web_settings: dictionary.
    '''
    if option == 'web':
        try:
            return project.web_settings
        except AttributeError:
            project.web_settings = init_websettings()   
            for key, item in project.web_settings.iteritems():
                if item:
                    project.web_settings[key] = item
            project.save()
            return project.web_settings
    else:
        pass


def list_records(request, project):
    form = RecordForm() # search form  
    loaded_prj = load_project() # project object
    sim_list = models.Record.objects.filter(project__id=project).order_by('-timestamp') # project: string
    web_settings = initSettings(loaded_prj)
    nb_per_page = int(web_settings['nb_records_per_page'])
    paginator = Paginator(sim_list, nb_per_page)
    files = os.listdir(os.getcwd()) # names of all files and folders in current directory
    page_list = paginator.page(1) # always open the first page
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
           'path':loaded_prj.default_executable.path}
    return render_to_response('record_list.html', dic)