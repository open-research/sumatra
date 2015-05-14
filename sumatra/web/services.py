"""
docstring goes here


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from builtins import object


from django import forms
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from sumatra.projects import load_project
from sumatra.recordstore.django_store import models
from time import strptime
import datetime
import os
import json
from functools import reduce
import itertools


def init_websettings():
    return {'nb_records_per_page': 10,
            'display_density': 'compact',
            'hidden_cols': None}


def unescape(label):
    return label.replace("||", "/")


class ProjectUpdateForm(forms.ModelForm):

    class Meta(object):
        model = models.Project
        fields = ('name', 'description')


class SearchForm(forms.ModelForm):

    ''' this class will be inherited after. It is for changing the 
    requirement properties for any field in the search form'''

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        for key, field in self.fields.items():
            self.fields[key].required = False


class RecordForm(SearchForm):
    executable = forms.ModelChoiceField(queryset=models.Executable.objects.all(), empty_label='')
    repository = forms.ModelChoiceField(queryset=models.Repository.objects.all(), empty_label='')
    timestamp = forms.DateTimeField(label="Date")

    class Meta(object):
        model = models.Record
        fields = ('label', 'tags', 'reason', 'executable', 'repository',
                  'main_file', 'timestamp')


class DefaultTemplate(object):

    '''
    Default template is the record_list.html. This class will be invoked each time user opens
    http://localhost/{{project_id}}/
    '''

    def __init__(self, project):
        self.nbCol = 14
        self.project_name = project
        self.form = RecordForm()
        self._init_settings()
        self.sim_list = models.Record.objects.filter(project__id=project).order_by(
            '-timestamp')  # here project is the string
        self.files = os.listdir(os.getcwd())
        self.active = 'List of records'
        self.tags = False  # tags is not defined

    def init_object_list(self, page=1):
        self.paginator = Paginator(self.sim_list, int(self.settings['nb_records_per_page']))
        try:
            self.page_list = self.paginator.page(page)
        except PageNotAnInteger:
            self.page_list = self.paginator.page(1)
        except EmptyPage:
            self.page_list = self.paginator.page(self.paginator.num_pages)  # deliver last page of results
        self.object_list = self.page_list.object_list

    def _init_settings(self):
        '''
        Checking existence of the specific settings in ~/.smtrc
        In case it doesn't exist, it will be initialized with some default values
        Inputs:
            project: project object,
            option: string.
        Output:
            web_settings: dictionary.
        '''
        global_conf_file = os.path.expanduser(os.path.join("~", ".smtrc"))
        if os.path.exists(global_conf_file):
            with open(global_conf_file) as fp:
                self.settings = json.load(fp)  # should really merge in any missing settings
                #print "record_hidden_cols: ", self.settings['record_hidden_cols']
        else:
            self.settings = init_websettings()

    def getDict(self):
        return self.__dict__



class DataTemplate(object):

    '''
    Default template is the record_list.html. This class will be invoked each time user opens
    http://localhost/{{project_id}}/
    '''

    def __init__(self, project):
        self.nbCol = 14
        self.project_name = project
        self.form = RecordForm()
        self._init_settings()
        self.sim_list = models.Record.objects.filter(project__id=project).order_by(
            '-timestamp')  # here project is the string

        self.data_list = models.DataKey.objects.all()

        self.files = os.listdir(os.getcwd())
        self.active = 'List of records'
        self.tags = False  # tags is not defined

    def init_object_list(self, page=1):
        self.paginator = Paginator(self.sim_list, int(self.settings['nb_records_per_page']))
        try:
            self.page_list = self.paginator.page(page)
        except PageNotAnInteger:
            self.page_list = self.paginator.page(1)
        except EmptyPage:
            self.page_list = self.paginator.page(self.paginator.num_pages)  # deliver last page of results
        self.object_list = self.page_list.object_list

    def _init_settings(self):
        '''
        Checking existence of the specific settings in ~/.smtrc
        In case it doesn't exist, it will be initialized with some default values
        Inputs:
            project: project object,
            option: string.
        Output:
            web_settings: dictionary.
        '''
        global_conf_file = os.path.expanduser(os.path.join("~", ".smtrc"))
        if os.path.exists(global_conf_file):
            with open(global_conf_file) as fp:
                self.settings = json.load(fp)  # should really merge in any missing settings
        else:
            self.settings = init_websettings()

    def getDict(self):

        # dkey = self.__dict__['data_list'][0]

        # print type(dkey)
        # print type(dkey.metadata)
        # print type(dkey.get_metadata())
        
        # >>> <class 'sumatra.recordstore.django_store.models.DataKey'>
        # >>> <type 'unicode'>
        # >>> <type 'dict'>

        return {'project_name': self.project_name, 'data_list': self.data_list}
 

class AjaxTemplate(DefaultTemplate):

    '''
    This class will be invoked only when the content of the table needs to be refreshed.
    It is a child of DefaultTemplate class
    '''

    # request_post=None when user retrieve the list of records for defined tag (views: list_tagged_records())
    def __init__(self, project, request_post=None):
        super(AjaxTemplate, self).__init__(project)
        if request_post:
            self.form = RecordForm(request_post)  # retrieving all fields of the search form
            self.page = request_post.get('page', 1)
            # date_base/date_interval are not part of the search form
            self.date_base = request_post.get('date_interval_from', False)
            self.date_interval = request_post.get('date_interval', False)
            self.tags = request_post.get('search_input[tags]', False)
            self.dict_dates = {'1 day': 1, '3 days': 3, '1 week': 7, '2 weeks': 14,
                               '1 month': 31, '2 months': 31 * 2, '6 months': 31 * 6, '1 year': 365}


    def save_settings(self):
        global_conf_file = os.path.expanduser(os.path.join("~", ".smtrc"))
        with open(global_conf_file, 'w') as fp:
            json.dump(self.settings, fp, indent=2)


class RecordUpdateForm(forms.ModelForm):
    wide_textarea = forms.Textarea(attrs={'rows': 2, 'cols': 80})
    reason = forms.CharField(required=False, widget=wide_textarea)
    outcome = forms.CharField(required=False, widget=wide_textarea)

    class Meta(object):
        model = models.Record
        fields = ('reason', 'outcome', 'tags')


class TagUpdateForm(forms.ModelForm):
    class Meta(object):
        model = models.Record
        fields = ('tags',)
