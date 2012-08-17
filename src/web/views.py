"""
Defines view functions and forms for the Sumatra web interface.
"""
import os
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import list_detail
from services import DefaultTemplate, AjaxTemplate, ProjectUpdateForm, RecordUpdateForm, unescape
from sumatra.recordstore.django_store.models import Project, Tag, Record
from sumatra.datastore import get_data_store
from sumatra.versioncontrol import get_working_copy
from sumatra.commands import run

def list_records(request, project):
    if request.is_ajax(): # only when paginating
        ajaxTempOb = AjaxTemplate(project, request.POST)
        if ajaxTempOb.form.is_valid():
            ajaxTempOb.filter_search(request.POST.dict()) # taking into consideration the search inquiry
            ajaxTempOb.init_object_list(ajaxTempOb.page) # taking into consideration pagination
            return render_to_response('content.html', ajaxTempOb.getDict()) # content.html is a part of record_list.html
        else:
            return HttpResponse('search form is not valid')
    else:
        defTempOb = DefaultTemplate(project)
        defTempOb.init_object_list() # object_list is used in record_list.html     
        return render_to_response('record_list.html', defTempOb.getDict())

def list_projects(request):
    projects = Project.objects.all()
    return list_detail.object_list(request, queryset=projects,
                                   template_name="project_list.html",
                                   extra_context={'active':'List of projects',
                                                  'project_name':projects[0]}) #returns the first project

def show_project(request, project):
    project = Project.objects.get(id=project)
    # notification is used after the form is successfully stored. In project_detail.html we use jGrowl for that
    dic = {'project_name': project, 'form': None, 'active':'About', 'notification':False} 
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
    if request.method == 'POST': # user define a tag name (by clicking it)
        ajaxTempOb = AjaxTemplate(project, request.POST)
        ajaxTempOb.filter_search(request.POST)
        ajaxTempOb.init_object_list()
        dic = ajaxTempOb.getDict()
        return render_to_response('content.html', dic)
    else:
        return render_to_response('tag_list.html', {'tags_list':Tag.objects.all(), 'project_name': project})

def record_detail(request, project, label):
    if label != 'nolabel':
        label = unescape(label)
        record = Record.objects.get(label=label, project__id=project) 
    if request.method == 'POST':
        if request.POST.has_key('delete'): # in this version the page record_detail doesn't have delete option
            record.delete() 
            return HttpResponseRedirect('.')
        elif request.POST.has_key('show_args'): # user clicks the link <parameters> in record_list.html
            parameter_set = record.parameters.to_sumatra()
            return HttpResponse(parameter_set)
        elif request.POST.has_key('show_script'): # retrieve script code from the repo
            digest = request.POST.get('digest', False)
            path = request.POST.get('path', False)
            path = str(path).encode("string_escape")
            wc = get_working_copy(path)
            file_content = wc.content(digest)
            return HttpResponse(file_content)
        elif request.POST.has_key('compare_records'):
            labels = request.POST.getlist('records[]', False)
            records = Record.objects.filter(project__id=project)
            records = records.filter(label__in=labels[:2]) # by now we take only two records
            dic = {'records':records}
            return render_to_response('comparison_framework.html', dic)
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
    return render_to_response('record_detail.html', {'record': record,
                                                     'project_name': project,
                                                     'parameters': parameter_set,
                                                     'form': form
                                                     })

def show_file(request, project, label):
    if request.POST.has_key('show_args'): # retrieve the content of the input file
        name = request.POST.get('name', False)
        if os.name == 'posix':
            arg_file = open(os.getcwd() + '/' + name, 'r')
        else:
            arg_file = open(os.getcwd() + '\\' + name, 'r')
        f_content = arg_file.read()
        arg_file.close()
        return HttpResponse(f_content)

def search(request, project):
    ajaxTempOb = AjaxTemplate(project, request.POST)
    if request.POST.has_key('fulltext_inquiry'): # using the input #search_subnav
        ajaxTempOb.filter_search(request.POST.dict())
        ajaxTempOb.init_object_list(ajaxTempOb.page) 
        return render_to_response('content.html', ajaxTempOb.getDict())
    else : # using the form   
        if ajaxTempOb.form.is_valid():
            ajaxTempOb.filter_search(ajaxTempOb.form.cleaned_data) # taking into consideration the search form
            ajaxTempOb.init_object_list(ajaxTempOb.page) # taking into consideration pagination
            return render_to_response('content.html', ajaxTempOb.getDict()) # content.html is a part of record_list.html
        else:
            return HttpResponse('search form is not valid')


def set_tags(request, project):
    records_to_settags = request.POST.get('selected_labels', False)
    if records_to_settags: # case of submit request
        records_to_settags = records_to_settags.split(',')
        records = Record.objects.filter(label__in=records_to_settags, project__id=project)
        for record in records:
            form = RecordUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
        return HttpResponseRedirect('.')

def delete_records(request, project):
    records_to_delete = request.POST.getlist('delete[]')
    delete_data = request.POST.get('delete_data', False)
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
    web_settings = {'display_density':request.POST.get('display_density', False),
                    'nb_records_per_page':request.POST.get('nb_records_per_page', False),
                    'hidden_cols': request.POST.getlist('hidden_cols[]', False)}
    ajaxTempOb = AjaxTemplate(project, None)
    for key, item in web_settings.iteritems():
        if item:
            ajaxTempOb.project.web_settings[key] = item
        else:
            if key == 'hidden_cols':
                ajaxTempOb.project.web_settings[key] = None
    ajaxTempOb.project.save()
    ajaxTempOb.init_object_list(1)
    return render_to_response('content.html', ajaxTempOb.getDict())

def run_sim(request, project):
    if request.POST.has_key('content'): # save the edited argument file
        content = request.POST.get('content', False) # in case user changed the argument file
        arg_file = request.POST.get('arg_file', False)
        if os.name == 'posix':
            fow = open(os.getcwd() + '/' + arg_file, 'w')
        else:
            fow = open(os.getcwd() + '\\' + arg_file, 'w')
        fow.write(content)
        fow.close()
        return HttpResponse('ok')
    else: # run simulation
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
        ajaxTempOb.init_object_list(1) # taking into consideration pagination
        return render_to_response('content.html', ajaxTempOb.getDict()) 