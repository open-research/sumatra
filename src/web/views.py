"""
Defines view functions and forms for the Sumatra web interface.
"""
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import list_detail
from services import DefaultTemplate, AjaxTemplate, ProjectUpdateForm, RecordUpdateForm, unescape
from sumatra.recordstore.django_store.models import Project, Tag, Record
from sumatra.datastore import get_data_store

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
    label = unescape(label)
    record = Record.objects.get(label=label, project__id=project) 
    if request.method == 'POST':
        if request.POST.has_key('delete'): # in this version the page record_detail doesn't have delete option
            record.delete() 
            return HttpResponseRedirect('.')
        elif request.POST.has_key('show_args'): # user clicks the link <parameters> in record_list.html
            parameter_set = record.parameters.to_sumatra()
            return HttpResponse(parameter_set)
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
    web_settings = {'display_density':request.POST.get('display_density', 'compact'),
                    'nb_records_per_page':request.POST.get('nb_records_per_page', 14),
                    'hidden_cols': request.POST.getlist('hidden_cols[]', False)}
    project_loaded = load_project()
    print web_settings['display_density']