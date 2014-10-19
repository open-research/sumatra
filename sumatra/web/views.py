"""
Defines view functions and forms for the Sumatra web interface.

:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import os
import os.path
import mimetypes
import csv
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.views.generic.list import ListView
try:
    from django.views.generic.dates import MonthArchiveView
except ImportError:  # older versions of Django
    MonthArchiveView = object
from services import DefaultTemplate, DataTemplate, AjaxTemplate, ProjectUpdateForm, RecordUpdateForm, TagUpdateForm, unescape
from sumatra.recordstore.django_store.models import Project, Tag, Record

from sumatra.projects import load_project
import sumatra.recordstore.django_store.models as models

from sumatra.datastore import get_data_store, DataKey
from sumatra.versioncontrol import get_working_copy
from sumatra.commands import run, configure
from sumatra.projects import load_project
from sumatra.programs import Executable

DEFAULT_MAX_DISPLAY_LENGTH = 10 * 1024
mimetypes.init()




def list_records(request, project):
    # if request.is_ajax():  # only when paginating
    #     ajaxTempOb = AjaxTemplate(project, request.POST)
    #     if ajaxTempOb.form.is_valid():
    #         ajaxTempOb.filter_search(request.POST)  # taking into consideration the search inquiry
    #         ajaxTempOb.init_object_list(ajaxTempOb.page)  # taking into consideration pagination
    #         # content.html is a part of record_list.html
    #         return render_to_response('content.html', ajaxTempOb.getDict())
    #     else:
    #         return HttpResponse('search form is not valid')
    # else:
    defTempOb = DefaultTemplate(project)
    defTempOb.init_object_list()  # object_list is used in record_list.html
    return render_to_response('record_list.html', defTempOb.getDict())



def compare_selected_records(request, project):
    '''
    render record comparison modal for the selected records
    '''
    selected_labels = request.GET.getlist('selection[]')
    records = Record.objects.filter(project__id=project,
                                    label__in=selected_labels)

    return render_to_response('comparison_window.html', {'records': records})


def list_data(request, project):
    defTempOb = DataTemplate(project)
    return render_to_response('data_list.html', defTempOb.getDict())


class ProjectListView(ListView):
    template_name = 'project_list.html'

    def get_queryset(self):
        return Project.objects.all()

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        projects = self.get_queryset()

        context['active'] = 'List of projects'
        if not len(projects):
            context['project_name'] = load_project().name
            if not load_project().default_executable:  # empty project: without any records inside
                context['show_modal'] = True
        else:
            context['project_name'] = projects[0]
        return context


def show_project(request, project):
    project = Project.objects.get(id=project)
    # notification is used after the form is successfully stored. In project_detail.html we use jGrowl for that
    dic = {'project_name': project, 'form': None, 'active': 'About', 'notification': False}
    if request.method == 'POST':
        form = ProjectUpdateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            dic['notification'] = True
            dic['form'] = form
            return render_to_response('project_detail.html', dic)
    else:
        dic['form'] = ProjectUpdateForm(instance=project)
    return render_to_response('project_detail.html', dic)


def list_tags(request, project):
    if request.method == 'POST':  # user define a tag name (by clicking it)
        ajaxTempOb = AjaxTemplate(project, request.POST)
        ajaxTempOb.filter_search(request.POST)
        ajaxTempOb.init_object_list()
        dic = ajaxTempOb.getDict()
        return render_to_response('content.html', dic)
    else:
        return render_to_response('tag_list.html', {'tags_list': Tag.objects.all(), 'project_name': project})


def record_detail(request, project, label):
    if label != 'nolabel':
        label = unescape(label)
        record = Record.objects.get(label=label, project__id=project)
    if request.method == 'POST':
        if request.POST.has_key('delete'):  # in this version the page record_detail doesn't have delete option
            record.delete()
            return HttpResponseRedirect('..')
        elif request.POST.has_key('show_args'):  # user clicks the link <parameters> in record_list.html
            parameter_set = record.parameters.to_sumatra()
            return HttpResponse(parameter_set)
        elif request.POST.has_key('show_script'):  # retrieve script code from the repo
            digest = request.POST.get('digest', False)
            path = request.POST.get('path', False)
            path = str(path).encode("string_escape")
            wc = get_working_copy(path)
            file_content = wc.content(digest)
            return HttpResponse(file_content)
        elif request.POST.has_key('compare_records'):
            labels = request.POST.getlist('records[]')
            records = Record.objects.filter(project__id=project)
            records = records.filter(label__in=labels[:2])  # by now we take only two records
            for record in records:
                if record.script_arguments == '<parameters>':
                    record.script_arguments = record.parameters.to_sumatra()
            dic = {'records': records}
            return render_to_response('comparison_framework.html', dic)
        else:
            form = RecordUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
    else:
        form = RecordUpdateForm(instance=record)
    # data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters)) doesn't get used?
    parameter_set = record.parameters.to_sumatra()
    if hasattr(parameter_set, "as_dict"):
        parameter_set = parameter_set.as_dict()
    return render_to_response('record_detail.html', {'record': record,
                                                     'project_name': project,
                                                     'parameters': parameter_set,
                                                     'form': form
                                                     })


def search(request, project):
    ajaxTempOb = AjaxTemplate(project, request.POST)
    if request.POST.has_key('fulltext_inquiry'):  # using the input #search_subnav
        ajaxTempOb.filter_search(request.POST)
        ajaxTempOb.init_object_list(ajaxTempOb.page)
        return render_to_response('content.html', ajaxTempOb.getDict())
    else:  # using the form
        if ajaxTempOb.form.is_valid():
            ajaxTempOb.filter_search(ajaxTempOb.form.cleaned_data)  # taking into consideration the search form
            ajaxTempOb.init_object_list(ajaxTempOb.page)  # taking into consideration pagination
            # content.html is a part of record_list.html
            return render_to_response('content.html', ajaxTempOb.getDict())
        else:
            return HttpResponse('search form is not valid')


def set_tags(request, project):
    records_to_settags = request.POST.get('selected_labels', False)
    if records_to_settags:  # case of submit request
        records_to_settags = records_to_settags.split(',')
        records = Record.objects.filter(label__in=records_to_settags, project__id=project)
        for record in records:
            form = TagUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
        return HttpResponseRedirect('.')


def delete_records(request, project):
    records_to_delete = request.POST.getlist('delete[]')
    delete_data = request.POST.get('delete_data', False)
    if isinstance(delete_data, basestring):
        # Convert strings returned from Javascript function into Python bools
        delete_data = {'false': False, 'true': True}[delete_data]
    records = Record.objects.filter(label__in=records_to_delete, project__id=project)
    if records:
        for record in records:
            if delete_data == True:
                datastore = record.datastore.to_sumatra()
                datastore.delete(*[data_key.to_sumatra()
                                   for data_key in record.output_data.all()])
            record.delete()
    return HttpResponse('OK')


def settings(request, project):
    # if request.POST.has_key('init_settings'):
    #     executable = request.POST.get('executable')
    #     try:
    #         Executable(executable)._find_executable(executable)
    #     except:
    #         return HttpResponse('error')
    #     configure(['--executable=%s' % executable])
    #     return HttpResponse('OK')
    # web_settings = {'display_density': request.POST.get('display_density', False),
    #                 'nb_records_per_page': request.POST.get('nb_records_per_page', False),
    #                 'hidden_cols': request.POST.getlist('hidden_cols[]')}

    print request
    print request.POST.getlist('record_hidden_cols[]')

    # ajaxTempOb = AjaxTemplate(project, None)
    # for key, item in web_settings.iteritems():
    #     if item:
    #         ajaxTempOb.settings[key] = item
    #     else:
    #         if key == 'hidden_cols':
    #             ajaxTempOb.settings[key] = None
    # ajaxTempOb.save_settings()
    # ajaxTempOb.init_object_list(1)
    # return render_to_response('content.html', ajaxTempOb.getDict())

    return list_records(request, project)


def run_sim(request, project):
    if request.POST.has_key('content'):  # save the edited argument file
        content = request.POST.get('content', False)  # in case user changed the argument file
        arg_file = request.POST.get('arg_file', False)
        if os.name == 'posix':
            fow = open(os.getcwd() + '/' + arg_file, 'w')
        else:
            fow = open(os.getcwd() + '\\' + arg_file, 'w')
        fow.write(content)
        fow.close()
        return HttpResponse('ok')
    else:  # run computation
        run_opt = {'--label': request.POST.get('label', False),
                   '--reason': request.POST.get('reason', False),
                   '--tag': request.POST.get('tag', False),
                   'exec': request.POST.get('execut', False),
                   '--main': request.POST.get('main_file', False),
                   'args': request.POST.get('args', False)}
        options_list = []
        for key, item in run_opt.iteritems():
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
        ajaxTempOb = AjaxTemplate(project)
        ajaxTempOb.init_object_list(1)  # taking into consideration pagination
        if len(Record.objects.filter(project__id=project)) == 1:
            return HttpResponse('OK')
        else:
            return render_to_response('content.html', ajaxTempOb.getDict())



def data_detail(request, project):

    path = request.GET['path']
    digest = request.GET['digest']
   
    data_keys = models.DataKey.objects.filter(path = path, digest = digest)

    if len(data_keys)==1:
        data_key = data_keys[0]
    elif len(data_keys)==0:
        print 'no such data_key'
    elif len(data_keys)>1:
        print 'duplicate error'

    return render_to_response("data_detail.html",
                              {'data_key': data_key, 'project_name': project})
    

   

def download_file(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    digest = request.GET['digest']
    data_key = DataKey(path, digest)
    record = Record.objects.get(label=label, project__id=project)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))

    mimetype, encoding = mimetypes.guess_type(path)
    try:
        content = data_store.get_content(data_key)
    except (IOError, KeyError):
        raise Http404
    dir, fname = os.path.split(path)
    response = HttpResponse(content_type=mimetype)
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    response.write(content)
    return response


def show_image(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    digest = request.GET['digest']
    type = request.GET.get('type', 'output')
    data_key = DataKey(path, digest)
    mimetype, encoding = mimetypes.guess_type(path)
    if mimetype in ("image/png", "image/jpeg", "image/gif", "image/x-png"):
        record = Record.objects.get(label=label, project__id=project)
        if type == 'output':
            data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
        else:
            data_store = get_data_store(record.input_datastore.type, eval(record.input_datastore.parameters))
        try:
            content = data_store.get_content(data_key)
        except (IOError, KeyError):
            raise Http404
        return HttpResponse(content, content_type=mimetype)
    else:
        return HttpResponse(content_type="image/png")  # should return a placeholder image?


def show_diff(request, project, label, package=''):
    label = unescape(label)
    record = Record.objects.get(label=label, project__id=project)
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


class Timeline(MonthArchiveView):
    date_field = 'timestamp'
    template_name = 'timeline.html'
    #paginate_by = 20

    def get_queryset(self):
        return Record.objects.filter(user__startswith=self.kwargs['user'])

    def get_context_data(self, **kwargs):
        context = super(Timeline, self).get_context_data(**kwargs)
        context['user_name'] = self.kwargs['user']
        return context

    # note there seems to be a bug with next_month and previous_month,
    # when the timestamp is the last day of the month
    # because django.views.generic.dates._get_next_prev_month is
    # comparing a datetime (the timestamp) to a date-cast-to-a-time, which
    # has an implicit time of 00:00
    # also see https://code.djangoproject.com/ticket/391
