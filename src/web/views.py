"""
Defines view functions and forms for the Sumatra web interface.
"""

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import list_detail
from django import forms
from tagging.views import tagged_object_list
from sumatra.recordstore.django_store import models
from sumatra.datastore import get_data_store
import mimetypes
mimetypes.init()
import csv
import os


def unescape(label):
    return label.replace("||", "/")

class TagSearch(forms.Form):
    search = forms.CharField() 
    
class RecordUpdateForm(forms.ModelForm):
    wide_textarea = forms.Textarea(attrs={'rows': 2, 'cols':80})
    reason = forms.CharField(required=False, widget=wide_textarea)
    outcome = forms.CharField(required=False, widget=wide_textarea)
    
    class Meta:
        model = models.Record
        fields=('reason', 'outcome', 'tags')

def list_projects(request):
    return list_detail.object_list(request, queryset=models.Project.objects.all(),
                                   template_name="project_list.html")

def show_project(request, project):
    project = models.Project.objects.get(id=project)
    return render_to_response('project_detail.html', {'project': project})
   
def list_records(request, project):
    search_form = TagSearch()
    return list_detail.object_list(request,
                                   queryset=models.Record.objects.filter(project__id=project),
                                   template_name="record_list.html",
                                   extra_context={
                                    'project_name': project,
                                    'search_form': search_form})  

def list_tagged_records(request, project, tag):
    queryset = models.Record.objects.filter(project__id=project)
    return tagged_object_list(request,
                              tag=tag,
                              queryset_or_model=queryset,
                              template_name="record_list.html",
                              extra_context={ 'project_name': project })

def record_detail(request, project, label):
    label = unescape(label)
    record = models.Record.objects.get(label=label, project__id=project)
    
    if request.method == 'POST':
        if request.POST.has_key('delete'):
            record.delete()
            return HttpResponseRedirect('/')
        else:
            form = RecordUpdateForm(request.POST, instance=record)
            if form.is_valid():
                form.save()
    else:
        form = RecordUpdateForm(instance=record)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
    datafiles = data_store.list_files(eval(record.data_key))
    assert isinstance(datafiles, list), type(datafiles)
    parameter_set = record.parameters.to_sumatra()
    if hasattr(parameter_set, "as_dict"):
        parameter_set = parameter_set.as_dict()
    return render_to_response('record_detail.html', {'record': record,
                                                     'project_name': project,
                                                     'parameters': parameter_set,
                                                     'datafiles': datafiles,
                                                     'form': form
                                                     })

def delete_records(request, project):
    records_to_delete = request.POST.getlist('delete')
    delete_data = 'delete_data' in request.POST
    records = models.Record.objects.filter(label__in=records_to_delete, project__id=project)
    for record in records:
        if delete_data:
            datastore = record.datastore.to_sumatra()
            data_key = eval(record.data_key)
            datastore.delete(data_key)
        record.delete()
    return HttpResponseRedirect('/')  


def list_tags(request, project):
    tags = {
        "extra_context": { 'project_name': project },
        "queryset": models.Tag.objects.all(),
        "template_name": "tag_list.html",
    }
    return list_detail.object_list(request, **tags)

DEFAULT_MAX_DISPLAY_LENGTH = 10*1024

def show_file(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    if 'truncate' in request.GET:
        if request.GET['truncate'].lower() == 'false':
            max_display_length = None
        else:
            max_display_length = int(request.GET['truncate'])*1024
    else:
        max_display_length = DEFAULT_MAX_DISPLAY_LENGTH
    
    record = models.Record.objects.get(label=label, project__id=project)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
    # check the file is in the store for a given simulation/analysis
        
    try:
        mimetype, encoding = mimetypes.guess_type(path)
        if mimetype  == "text/csv":
            content = data_store.get_content(record.data_key, path, max_length=max_display_length)
            truncated = False
            if max_display_length is not None and len(content) >= max_display_length:
                truncated = True
                
                # dump the last truncated line (if any)
                content = content.rpartition('\n')[0]

            lines = content.splitlines()
            reader = csv.reader(lines)
            
            return render_to_response("show_csv.html",
                                      {'path': path, 'label': label,
                                       'project_name': project,
                                       'reader': reader,
                                       'truncated':truncated
                                       })

        elif mimetype == None or mimetype.split("/")[0] == "text":
            content = data_store.get_content(record.data_key, path, max_length=max_display_length)
            truncated = False
            if max_display_length is not None and len(content) >= max_display_length:
                truncated = True
            return render_to_response("show_file.html",
                                      {'path': path, 'label': label,
                                       'project_name': project,
                                       'content': content,
                                       'truncated': truncated,
                                       })
        elif mimetype in ("image/png", "image/jpeg", "image/gif"):
            return render_to_response("show_image.html",
                                      {'path': path, 'label': label,
                                       'project_name': project,})
        #elif mimetype == 'application/zip':
        #    import zipfile
        #    if zipfile.is_zipfile(path):
        #        zf = zipfile.ZipFile(path, 'r')
        #        contents = zf.namelist()
        #        zf.close()
        #        return render_to_response("show_file.html",
        #                              {'path': path, 'label': label,
        #                               'content': "\n".join(contents)
        #                               })
        #    else:
        #        raise IOError("Not a valid zip file")
        else:
            return render_to_response("show_file.html", {'path': path, 'label': label,
                                                         'project_name': project,
                                                         'content': "Can't display this file (mimetype assumed to be %s)" % mimetype})
    except IOError, e:
        return render_to_response("show_file.html", {'path': path, 'label': label,
                                                     'project_name': project,
                                                     'content': "File not found.",
                                                     'errmsg': e})

def download_file(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    
    record = models.Record.objects.get(label=label, project__id=project)
    data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))

    mimetype, encoding = mimetypes.guess_type(path)
    content = data_store.get_content(record.data_key, path)
    
    dir, fname = os.path.split(path) 
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] =  'attachment; filename=%s' % fname
    response.write(content)
    return response 

def show_image(request, project, label):
    label = unescape(label)
    path = request.GET['path']
    mimetype, encoding = mimetypes.guess_type(path)
    if mimetype in ("image/png", "image/jpeg", "image/gif"):
        record = models.Record.objects.get(label=label, project__id=project)
        data_store = get_data_store(record.datastore.type, eval(record.datastore.parameters))
        content = data_store.get_content(record.data_key, path)
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
    
