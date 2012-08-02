"""
Defines view functions and forms for the Sumatra web interface.
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response
from services import DefaultTemplate, filter_search


def list_records(request, project):
    if request.is_ajax(): # only when paginating
        page = request.POST.get('page', False)    
        form = RecordForm(request.POST) # retrieving all fields of the search form
        date_from = request.POST.get('date_interval_from',False) # date_from and date_interval are not part of the search form
        date_interval = request.POST.get('date_interval',False)
        if form.is_valid():
            request_data = form.cleaned_data
            sim_list = filter_search(sim_list, request_data, date_from, date_interval)
            paginator = Paginator(sim_list, nb_per_page)   
        try:
            page_list = paginator.page(page)
        except PageNotAnInteger:
            page_list = paginator.page(1)
        except EmptyPage:          
            page_list = paginator.page(paginator.num_pages) # deliver last page of results
        dic = {'project_name': project,
               'form': form,
               'settings':web_settings,
               'paginator':paginator,
               'object_list':page_list.object_list,
               'page_list':page_list,
               'width':rendered_width}
        return render_to_response('content.html', dic)
    else:
        defTempOb = DefaultTemplate(project)     
        return render_to_response('record_list.html', defTempOb.getDict())