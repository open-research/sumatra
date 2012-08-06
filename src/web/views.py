"""
Defines view functions and forms for the Sumatra web interface.
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.generic import list_detail
from services import DefaultTemplate, AjaxTemplate, ProjectUpdateForm
from sumatra.recordstore.django_store.models import Project, Tag, Record

def list_records(request, project):
    if request.is_ajax(): # only when paginating
        ajaxTempOb = AjaxTemplate(project, request.POST)
        if ajaxTempOb.form.is_valid():
            ajaxTempOb.filter_search(ajaxTempOb.form.cleaned_data) # taking into consideration the search form
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