"""
Defines view functions and forms for the Sumatra web interface.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from builtins import str
from past.utils import old_div

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django import forms
import json
from django.core.paginator import Paginator
from sumatra.recordstore.django_store import models
from sumatra.datastore import get_data_store, DataKey
from sumatra.commands import run
from sumatra.versioncontrol import get_repository
from sumatra.projects import load_project, init_websettings
from sumatra.versioncontrol._mercurial import content_mercurial
from sumatra.versioncontrol._mercurial import MercurialRepository
import mimetypes
mimetypes.init()
import csv
import os

RECORDS_PER_PAGE = 50
'''
class SearchForm(forms.ModelForm):
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

def filter_search(request_data, date_from=False, date_interval=False):
    results =  models.Record.objects.all()
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

def search(request, project):
    if request.method == 'POST':
        web_settings = load_project().web_settings
        nb_per_page = int(load_project().web_settings['nb_records_per_page'])
        # form = RecordForm(request.POST)
        date_from = request.POST.get('date_interval_from',False)
        date_interval = request.POST.get('date_interval',False)
        form = RecordForm(request.POST)
        if form.is_valid():
            labels_list = {}
            request_data = form.cleaned_data
            #print request_data
            results = filter_search(request_data, date_from, date_interval)
            nbCols = 14
            paginator = Paginator(results, nb_per_page)
            nbCols_actual = nbCols - len(web_settings['table_HideColumns'])
            head_width = '%s%s' %(90.0/nbCols_actual, '%')
            if (nbCols_actual > 10):
                label_width = '150px'
            else:
                label_width = head_width
            page_list = paginator.page(1)
            dic = {'project_name': project,
                   #'form': form,
                   'settings':web_settings,
                   'paginator':paginator,
                   'object_list':page_list.object_list,
                   'page_list':page_list,
                   'width':{'head': head_width, 'label':label_width}}
            return render_to_response('content.html', dic)

def unescape(label):
    return label.replace("||", "/")
'''
class TagSearch(forms.Form):
    search = forms.CharField()
'''
class RecordUpdateForm(forms.ModelForm):
    wide_textarea = forms.Textarea(attrs={'rows': 2, 'cols':80})
    reason = forms.CharField(required=False, widget=wide_textarea)
    outcome = forms.CharField(required=False, widget=wide_textarea)

    class Meta:
        model = models.Record
        fields=('reason', 'outcome', 'tags')
'''
'''
class ProjectUpdateForm(forms.ModelForm):

    class Meta:
        model = models.Project
        fields = ('name', 'description')


def list_projects(request):
    projects = models.Project.objects.all()
    return list_detail.object_list(request, queryset=projects,
                                   template_name="project_list.html",
                                   extra_context={'active':'List of projects',
                                                  'project_name':projects[0]}) #returns the first project

def show_project(request, project):
    project = models.Project.objects.get(id=project)
    if request.method == 'POST':
        form = ProjectUpdateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
    else:
        form = ProjectUpdateForm(instance=project)
    return render_to_response('project_detail.html',
                              {'project_name': project, 'form': form, 'active':'About'})

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
    if request.is_ajax(): # when paginating
        page = request.POST.get('page', False)
        nbCols_actual = nbCols - len(web_settings['table_HideColumns'])
        head_width = '%s%s' %(90.0/nbCols_actual, '%')
        date_from = request.POST.get('date_interval_from',False)
        date_interval = request.POST.get('date_interval',False)
        if (nbCols_actual > 10):
            label_width = '150px'
        else:
            label_width = head_width
        form = RecordForm(request.POST)
        if form.is_valid():
            request_data = form.cleaned_data
            sim_list = filter_search(request_data, date_from, date_interval)
            paginator = Paginator(sim_list, nb_per_page)
        try:
            page_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_list = paginator.page(paginator.num_pages)
        dic = {'project_name': project,
               'form': form,
               'settings':web_settings,
               'paginator':paginator,
               'object_list':page_list.object_list,
               'page_list':page_list,
               'width':{'head': head_width, 'label':label_width}}
        return render_to_response('content.html', dic)

    else:
        # get names of all files in the current directory:
        files = os.listdir(os.getcwd())
        page_list = paginator.page(1)
        if web_settings['table_HideColumns'] is not None:
            nbCols_actual = nbCols - len(web_settings['table_HideColumns'])
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
    '''
"""
def list_tagged_records(request, project, tag):
    queryset = models.Record.objects.filter(project__id=project)
    return tagged_object_list(request,
                              tag=tag,
                              queryset_or_model=queryset,
                              template_name="record_list.html",
                              extra_context={'project_name': project })
"""
'''
def set_tags(request, project):
    records_to_settags = request.POST.get('selected_labels', False)
    if records_to_settags: # case of submit request
        records_to_settags = records_to_settags.split(',')
        records = models.Record.objects.filter(label__in=records_to_settags, project__id=project)
        for record in records:
            form = RecordUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
        return HttpResponseRedirect('.')
    return render_to_response('set_tag.html', {'form':form})
    '''
'''
def record_detail(request, project, label):
    label = unescape(label)
    record = models.Record.objects.get(label=label, project__id=project)
    if request.method == 'POST':
        if request.POST.has_key('delete'):
            record.delete() # need to add option to delete data
            return HttpResponseRedirect('.')
        else:
            form = RecordUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
    else:
        form = RecordUpdateForm(instance=record)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
    parameter_set = record.parameters.to_sumatra()
    if hasattr(parameter_set, "as_dict"):
        parameter_set = parameter_set.as_dict()
    return render_to_response('analysis_modal.html', {'record': record,
                                                     'project_name': project,
                                                     'parameters': parameter_set,
                                                     'form': form
                                                     })
'''
'''
def delete_records(request, project):
    records_to_delete = request.POST.getlist('delete[]')
    #delete_data = 'delete_data' in request.POST
    delete_data = request.POST.get('delete_data', False)
    records = models.Record.objects.filter(label__in=records_to_delete, project__id=project)
    for record in records:
        if delete_data:
            datastore = record.datastore.to_sumatra()
            datastore.delete(*[data_key.to_sumatra()
                               for data_key in record.output_data.all()])

        record.delete()
    return HttpResponse('')
'''
'''
def list_tags(request, project):
    tags = {
        "extra_context": { 'project_name': project },
        "queryset": models.Tag.objects.all(),
        "template_name": "tag_list.html",
    }
    return list_detail.object_list(request, **tags)
'''
DEFAULT_MAX_DISPLAY_LENGTH = 10*1024

def show_file(request, project, label):
    show_script = request.GET.get('show_script', False)
    show_args = request.GET.get('show_args', False)
    digest = request.GET.get('digest', False)
    name = request.GET.get('name', False) # file name (in case of argument file)
    path = request.GET.get('path', False)
    path = str(path).encode("string_escape")
    if show_script: # record_list.html: user click the main file cell
        if isinstance(get_repository(path), GitRepository):
            file_content = content_git(path, digest)
            return HttpResponse(file_content)
        elif isinstance(get_repository(path), MercurialRepository):
            file_content = content_mercurial(path, digest)
            return HttpResponse(file_content)
        return HttpResponse('Sorry, I cannot show you the content. Work only with GIT and Mercurial...')
    elif show_args:
        if 'fakepath' in name: # true for chrome
            name = name.split('\\')[-1]  # only for windows ???
        try:
            arg_file = open(os.getcwd() + '\\' + name, 'r')
            f_content = arg_file.read()
            arg_file.close()
        except:
            return HttpResponse('There is no file with this name in %s' %(os.getcwd()))
        return HttpResponse(f_content)


def show_file(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    digest = request.GET['digest']
    type = request.GET.get('type', 'output')
    show_script = request.GET.get('show_script', False)
    data_key = DataKey(path, digest)
    if show_script: # record_list.html: user click the main file cell
        print('digest: %s' %digest)
    if 'truncate' in request.GET:
        if request.GET['truncate'].lower() == 'false':
            max_display_length = None
        else:
            max_display_length = int(request.GET['truncate'])*1024
    else:
        max_display_length = DEFAULT_MAX_DISPLAY_LENGTH

    record = models.Record.objects.get(label=label, project__id=project)
    if type == 'output':
        data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
    else:
        data_store = get_data_store(record.input_datastore.type, eval(record.input_datastore.parameters))
    truncated = False
    mimetype, encoding = mimetypes.guess_type(path)
    try:
        if mimetype  == "text/csv":
            content = data_store.get_content(data_key, max_length=max_display_length)
            if max_display_length is not None and len(content) >= max_display_length:
                truncated = True

                # dump the last truncated line (if any)
                content = content.rpartition('\n')[0]

            lines = content.splitlines()
            reader = csv.reader(lines)

            return render_to_response("show_csv.html",
                                      {'path': path, 'label': label,
                                       'digest': digest,
                                       'project_name': project,
                                       'reader': reader,
                                       'truncated':truncated
                                       })

        elif mimetype == None or mimetype.split("/")[0] == "text":
            content = data_store.get_content(data_key, max_length=max_display_length)
            if max_display_length is not None and len(content) >= max_display_length:
                truncated = True
            return render_to_response("show_file.html",
                                      {'path': path, 'label': label,
                                       'digest': digest,
                                       'project_name': project,
                                       'content': content,
                                       'truncated': truncated,
                                       })
        elif mimetype in ("image/png", "image/jpeg", "image/gif"): # need to check digests match
            return render_to_response("show_image.html",
                                      {'path': path, 'label': label,
                                       'digest': digest,
                                       'project_name': project,})
        elif mimetype == 'application/zip':
            import zipfile
            if zipfile.is_zipfile(path):
                zf = zipfile.ZipFile(path, 'r')
                contents = zf.namelist()
                zf.close()
                return render_to_response("show_file.html",
                                      {'path': path, 'label': label,
                                       'content': "\n".join(contents)
                                       })
            else:
                raise IOError("Not a valid zip file")
        else:
            return render_to_response("show_file.html", {'path': path, 'label': label,
                                                         'project_name': project,
                                                         'content': "Can't display this file (mimetype assumed to be %s)" % mimetype})
    except (IOError, KeyError) as e:
        return render_to_response("show_file.html", {'path': path, 'label': label,
                                                     'project_name': project,
                                                     'content': "File not found.",
                                                     'errmsg': e})

def download_file(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    digest = request.GET['digest']
    data_key = DataKey(path, digest)
    record = models.Record.objects.get(label=label, project__id=project)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))

    mimetype, encoding = mimetypes.guess_type(path)
    try:
        content = data_store.get_content(data_key)
    except (IOError, KeyError):
        raise Http404
    dir, fname = os.path.split(path)
    response = HttpResponse(mimetype=mimetype)
    response['Content-Disposition'] =  'attachment; filename=%s' % fname
    response.write(content)
    return response

def show_image(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    digest = request.GET['digest']
    data_key = DataKey(path, digest)
    mimetype, encoding = mimetypes.guess_type(path)
    if mimetype in ("image/png", "image/jpeg", "image/gif"):
        record = models.Record.objects.get(label=label, project__id=project)
        data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
        try:
            content = data_store.get_content(data_key)
        except (IOError, KeyError):
            raise Http404
        response = HttpResponse(mimetype=mimetype)
        response.write(content)
        return response
    else:
        return HttpResponse(mimetype="image/png") # should return a placeholder image?

def show_diff(request, project, label, package):
    label = unescape(label)
    record = models.Record.objects.get(label=label, project__id=project)
    if package:
        dependency = record.dependencies.get(name=package)
    else:
        package = "Main script"
        dependency = record
    return render_to_response("show_diff.html", {'label': label,
                                                 'project_name': project,
                                                 'package': package,
                                                 'parent_version': dependency.version,
                                                 'diff': dependency.diff})

def run_sim(request, project):
    run_opt = {'--label': request.POST.get('label', False),
               '--reason': request.POST.get('reason', False),
               '--tag': request.POST.get('tag', False),
               'exec': request.POST.get('execut', False),
               '--main': request.POST.get('main_file', False),
               'args': request.POST.get('args', False)
              }
    content = request.POST.get('content', False) # in case user changed the argument file
    arg_file = request.POST.get('arg_file', False)
    if content:
        fow = open(os.getcwd() + '/' + arg_file, 'w')
        fow.write(content)
        fow.close()
        return HttpResponse('ok')
    options_list = []
    for key, item in run_opt.items():
        if item:
            if key == 'args':
                options_list.append(item)
            elif key == 'exec':
                executable = str(os.path.basename(item))
                if '.exe' in executable:
                    executable = executable.split('.')[0]
                options_list.append('='.join(['--executable', executable]))
            else:
                options_list.append('='.join([key, item]))
    run(options_list)
    records = models.Record.objects.order_by('-db_id')
    '''
    if not(len(record.launch_mode.get_parameters())):
        nbproc = 1
    repo_short = short_repo(record.repository.url)
    version_short = short_version(record.version)
    timestamp = record.timestamp
    date = timestamp.strftime("%d/%m/%Y")
    time = timestamp.strftime("%H:%M:%S")
    to_sumatra = {'Label-t':record.label,
                  'Tag-t':record.tags,
                  'Reason-t':record.reason,
                  'Outcome-t':record.outcome,
                  'Duration-t':filters.human_readable_duration(record.duration),
                  'Processes-t':nbproc,
                  'Name-t':record.executable.name,
                  'Version-t':record.executable.version,
                  'Repository-t':repo_short,
                  'Main_file-t':record.main_file,
                  'S-Version-t':version_short,
                  'Arguments-t':record.script_arguments,
                  'Date-t':date,
                  'Time-t':time}
    return HttpResponse(json.dumps(to_sumatra))
    '''
    paginator = Paginator(records, int(load_project().web_settings['nb_records_per_page']))
    page_list = paginator.page(1)
    dic = {'project_name': project,
           'settings':load_project().web_settings,
           'paginator':paginator,
           'object_list':page_list.object_list,
           'page_list':page_list}
    return render_to_response('content.html', dic)

def settings(request, project):
    ''' Only one of the following parameter can be True
    web_settings['saveSettings'] == True: save the settings in .smt/project
    web_settings['web'] == True: send project.web_settings to record_list.html
    web_settings['sumatra'] = True: send some spacific settings to record_list.html (they will
    be used in the popup window for the new record as the default values
    '''
    web_settings = {'display_density':request.POST.get('display_density', False),
                    'nb_records_per_page':request.POST.get('nb_records_per_page', False),
                    'table_HideColumns': request.POST.getlist('table_HideColumns[]'),
                    'saveSettings':request.POST.get('saveSettings', False),
                    'web':request.POST.get('web', False),
                    'sumatra':request.POST.get('sumatra', False)
                    }
    nbCols = 14  # total number of columns
    sim_list = models.Record.objects.filter(project__id=project).order_by('-timestamp')
    project_loaded = load_project()
    if web_settings['saveSettings']:
        if len(web_settings['table_HideColumns']) == 0:  # empty set (all checkboxes are checked)
            project_loaded.web_settings['table_HideColumns'] = []
        try:
            project_loaded.web_settings
        except(AttributeError, KeyError): # project doesn't have web_settings yet
            # upgrading of .smt/project: new supplementary settings entries
            project_loaded.web_settings = init_websettings()
        for key, item in web_settings.items():
            if item:
                project_loaded.web_settings[key] = item
        project_loaded.save()
        # repetition of code for list_records !!!
        nb_per_page = int(web_settings['nb_records_per_page'])
        paginator = Paginator(sim_list, nb_per_page)
        page_list = paginator.page(1)
        nbCols_actual = nbCols - len(web_settings['table_HideColumns'])
        head_width = '%s%s' %(old_div(90.0,nbCols_actual), '%')
        if (nbCols_actual > 10):
            label_width = '150px'
        else:
            label_width = head_width
        dic = {'project_name': project,
               'settings':project_loaded.web_settings,
               'paginator':paginator,
               'object_list':page_list.object_list,
               'page_list':page_list,
               'width':{'head': head_width, 'label':label_width}}
        return render_to_response('content.html', dic)
    elif web_settings['web']:
        return HttpResponse(json.dumps(project.web_settings))
    elif web_settings['sumatra']:
        settings = {'execut':project.default_executable.path,
                    'mfile':project.default_main_file}
        return HttpResponse(json.dumps(settings))
