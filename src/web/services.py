from django import forms
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from sumatra.projects import load_project, init_websettings
from sumatra.projects import init_websettings
from sumatra.recordstore.django_store import models
import datetime
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

class DefaultTemplate(object):
    ''' Default template is the record_list.html. THis class will be invoked each time user opens
    http://localhost/{{project_name}}/ '''
    def __init__(self, project):
        self.nbCol = 14
        self.project_name = project
        self.project = load_project()
        self.form = RecordForm()
        self.web_settings = self.initSettings()
        self.nb_per_page = int(self.web_settings['nb_records_per_page'])
        self.sim_list = models.Record.objects.filter(project__id=project).order_by('-timestamp') # here project is the string
        self.paginator = Paginator(self.sim_list, self.nb_per_page)
        self.page_list = self.paginator.page(1)
        self.files = os.listdir(os.getcwd())
        self.active = 'List of records'
        self.width = self.renderColWidth()
        self.path = self.project.default_executable.path
        self.object_list = self.page_list.object_list

    def renderColWidth(self):
        '''For calculating the width of the columns. These values will be send to .css
        Maybe it should rather be done using javascript?'''
        rendered_width = {}
        if self.web_settings['table_HideColumns'] is not None:
            nbCols_actual = self.nbCol - len(self.web_settings['table_HideColumns'])
        else:
            nbCols_actual = self.nbCol
        rendered_width['head'] = '%s%s' %(90.0/nbCols_actual, '%') # all columns except 'Label' since it should have bigger width
        if (nbCols_actual > 10):
            rendered_width['label'] = '150px'
        else:
            rendered_width['label'] = head_width
        return rendered_width

    def initSettings(self, option='web'):
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
                return self.project.web_settings
            except AttributeError:
                self.project.web_settings = init_websettings()   
                for key, item in self.project.web_settings.iteritems():
                    if item:
                        self.project.web_settings[key] = item
                self.project.save()
                return self.project.web_settings
        else:
            pass

    def getDict(self):
        return self.__dict__


class AjaxTemplate(DefaultTemplate):
    ''' This class will be invoked only when the content of the table needs to be refreshed '''
    def __init__(self, **argvs):
        pass

def filter_search(results, request_data, date_from=False, date_interval=False):
    for key, val in request_data.iteritems():
        if key in ['label','tags','reason', 'main_file', 'script_arguments']:
            field_list = [x.strip() for x in val.split(',')] 
            results =  results.filter(reduce(lambda x, y: x | y,
                                      [Q(**{"%s__contains" % key: word}) for word in field_list])) # __icontains (?)
        elif isinstance(val, datetime.date):
            results =  results.filter(timestamp__year = val.year,
                                      timestamp__month = val.month, 
                                      timestamp__day = val.day)
        elif isinstance(val, models.Executable):
            results =  results.filter(executable__path = val.path)

        elif isinstance(val, models.Repository):
            results =  results.filter(repository__url = val.url)
    if date_from: # in case user specifies "date within" in the search field
        date_from = strptime(date_from, "%m/%d/%Y") # from text input in the search form
        base = datetime.date(date_from.tm_year, date_from.tm_mon, date_from.tm_mday)
        dict_dates = {'1 day': 1, '3 days': 3, '1 week': 7, '2 weeks': 14, '1 month': 31, '2 months':31*2, '6 months':31*6, '1 year':365}
        nb_days = dict_dates[date_interval] # date interval went from the search form
        dateIntvl = {'min': base - datetime.timedelta(days = nb_days),
                     'max': base + datetime.timedelta(days = nb_days)} # interval of the dates
        results = filter(lambda x: x.timestamp >= datetime.datetime.combine(dateIntvl['min'], datetime.time()) and
                                   x.timestamp <= datetime.datetime.combine(dateIntvl['max'], datetime.time(23,59)), results) # all the records inside the specified interval
    return results