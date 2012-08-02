"""
Defines view functions and forms for the Sumatra web interface.
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response
from services import DefaultTemplate, AjaxTemplate


def list_records(request, project):
    if request.is_ajax(): # only when paginating
        ajaxTempOb = AjaxTemplate(project, request.POST)
        if ajaxTempOb.form.is_valid(): # is search form is ok
            ajaxTempOb.filter_search(ajaxTempOb.form.cleaned_data) # taking into consideration the search form
            ajaxTempOb.init_object_list(ajaxTempOb.page) # taking into consideration pagination
            return render_to_response('content.html', ajaxTempOb.getDict()) # content.html is a part of record_list.html
        else:
            return HttpResponse('search form is not valid')
    else:
        defTempOb = DefaultTemplate(project)
        defTempOb.init_object_list() # object_list is used in record_list.html     
        return render_to_response('record_list.html', defTempOb.getDict())