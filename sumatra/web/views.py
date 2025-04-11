"""
Defines views for the Sumatra web interface.

:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import parameters
import mimetypes
from django.conf import settings as django_settings
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.generic.list import ListView
try:
    from django.views.generic.dates import MonthArchiveView
except ImportError:  # older versions of Django
    MonthArchiveView = object

import json
import os
from django.views.generic import View, DetailView, TemplateView
from django.db.models import Q
from tagging.models import Tag
from sumatra.recordstore.serialization import datestring_to_datetime
from sumatra.recordstore.django_store.models import Project, Record, DataKey, Datastore
from sumatra.records import RecordDifference

DEFAULT_MAX_DISPLAY_LENGTH = 10 * 1024
global_conf_file = os.path.expanduser(os.path.join("~", ".smtrc"))
mimetypes.init()


class ProjectListView(ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'project_list.html'


class ProjectDetailView(DetailView):
    context_object_name = 'project'
    template_name = 'project_detail.html'

    def get_object(self):
        return Project.objects.get(pk=self.kwargs["project"])

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context['read_only'] = django_settings.READ_ONLY
        return context

    def post(self, request, *args, **kwargs):
        if django_settings.READ_ONLY:
            return HttpResponse('It is in read-only mode.')
        name = request.POST.get('name', None)
        description = request.POST.get('description', None)
        project = self.get_object()
        if description is not None:
            project.description = description
            project.save()
        if name is not None:
            project.name = name
            project.save()
        return HttpResponse('OK')


class RecordListView(ListView):
    context_object_name = 'records'
    template_name = ['record_list.html','record_list_serverside.html'][django_settings.SERVERSIDE]

    def get_queryset(self):
        return Record.objects.filter(project__id=self.kwargs["project"]).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super(RecordListView, self).get_context_data(**kwargs)
        context['project'] = Project.objects.get(pk=self.kwargs["project"])
        context['tags'] = Tag.objects.all()  # would be better to filter, to return only tags used in this project.
        context['read_only'] = django_settings.READ_ONLY
        return context


def unescape(label):
    return label.replace("||", "/")


class RecordDetailView(DetailView):
    context_object_name = 'record'
    template_name = 'record_detail.html'

    def get_object(self):
        label = unescape(self.kwargs["label"])
        return Record.objects.get(label=label, project__id=self.kwargs["project"])

    def get_context_data(self, **kwargs):
        context = super(RecordDetailView, self).get_context_data(**kwargs)
        context['project_name'] = self.kwargs["project"]  # use project full name?
        parameter_set = self.object.parameters.to_sumatra()
        if hasattr(parameter_set, "as_dict"):
            parameter_set = parameter_set.as_dict()
        context['parameters'] = parameter_set
        context['read_only'] = django_settings.READ_ONLY
        return context

    def post(self, request, *args, **kwargs):
        if django_settings.READ_ONLY:
            return HttpResponse('It is in read-only mode.')
        record = self.get_object()
        for attr in ("reason", "outcome", "tags"):
            value = request.POST.get(attr, None)
            if value is not None:
                setattr(record, attr, value)
        record.save()
        return HttpResponse('OK')


class DataListView(ListView):
    context_object_name = 'data_keys'
    template_name = ['data_list.html','data_list_serverside.html'][django_settings.SERVERSIDE]

    def get_queryset(self):
        return DataKey.objects.filter(Q(output_from_record__project_id=self.kwargs["project"]) |
                                      Q(input_to_records__project_id=self.kwargs["project"])).distinct()

    def get_context_data(self, **kwargs):
        context = super(DataListView, self).get_context_data(**kwargs)
        context['project'] = Project.objects.get(pk=self.kwargs["project"])
        return context


class DataDetailView(DetailView):
    context_object_name = 'data_key'

    def get_object(self):
        attrs = dict(path=self.request.GET['path'],
                     digest=self.request.GET['digest'],
                     creation=datestring_to_datetime(self.request.GET['creation']))
        return DataKey.objects.get(**attrs)

    def get_context_data(self, **kwargs):
        context = super(DataDetailView, self).get_context_data(**kwargs)
        context['project_name'] = self.kwargs["project"]  # use project full name?

        if 'truncate' in self.request.GET:
            if self.request.GET['truncate'].lower() == 'false':
                max_display_length = None
            else:
                max_display_length = int(self.request.GET['truncate']) * 1024
        else:
            max_display_length = DEFAULT_MAX_DISPLAY_LENGTH

        datakey = self.object
        mimetype = datakey.to_sumatra().metadata["mimetype"]
        try:
            datastore = datakey.output_from_record.datastore
        except AttributeError:
            datastore = datakey.input_to_records.first().input_datastore
        context['datastore_id'] = datastore.pk

        content_dispatch = {
            "text/csv": self.handle_csv,
            "text/plain": self.handle_plain_text,
            "application/zip": self.handle_zipfile
        }
        if mimetype in content_dispatch:
            content = datastore.to_sumatra().get_content(datakey.to_sumatra(),
                                                         max_length=max_display_length)
            context['truncated'] = (max_display_length is not None
                                    and len(content) >= max_display_length)

            context = content_dispatch[mimetype](context, content)
        return context

    def handle_csv(self, context, content):
        import csv
        content = content.rpartition('\n')[0]
        lines = content.splitlines()
        context['reader'] = csv.reader(lines)
        return context

    def handle_plain_text(self, context, content):
        context["content"] = content
        return context

    def handle_zipfile(self, context, content):
        import io
        import zipfile
        fp = io.StringIO(content)
        if zipfile.is_zipfile(fp):
            zf = zipfile.ZipFile(fp, 'r')
            contents = zf.namelist()
            zf.close()
        context["content"] = "\n".join(contents)

    def get_template_names(self):
        datakey = self.object.to_sumatra()
        mimetype = datakey.metadata["mimetype"]
        mimetype_guess, encoding = mimetypes.guess_type(datakey.path)

        if encoding == 'gzip':
            raise NotImplementedError("to be reimplemented")

        template_dispatch = {
            "image/png": 'data_detail_image.html',
            "image/jpeg": 'data_detail_image.html',
            "image/gif": 'data_detail_image.html',
            "image/x-png": 'data_detail_image.html',
            "text/csv": 'data_detail_csv.html',
            "text/plain": 'data_detail_text.html',
            "application/zip": 'data_detail_zip.html'
        }
        template_name = template_dispatch.get(mimetype, 'data_detail_base.html')
        return template_name


class ImageListView(ListView):
    context_object_name = 'data_keys'
    template_name = ['image_list.html','image_list_serverside.html'][django_settings.SERVERSIDE]

    def get_queryset(self):
        return DataKey.objects \
            .filter(output_from_record__project_id=self.kwargs["project"]) \
            .filter(metadata__contains='image')

    def get_context_data(self, **kwargs):
        context = super(ImageListView, self).get_context_data(**kwargs)
        context['project'] = Project.objects.get(pk=self.kwargs["project"])
        context['tags'] = Tag.objects.all()  # would be better to filter, to return only tags used in this project.
        return context


def image_thumbgrid(request, project):
    project_obj = Project.objects.get(id=project)
    if request.is_ajax():
        offset = int(request.GET.get('offset',0))
        limit = int(request.GET.get('limit',8))
        selected_tag = request.GET.get('selected_tag', 'None')
        if selected_tag != 'None':
            record_all = Record.objects.filter(project_id=project, tags__contains=selected_tag)
        else:
            record_all = Record.objects.filter(project_id=project)

        data = []
        for record in record_all:
            tags = [tag.name for tag in record.tag_objects()]
            for data_key in record.output_data.filter(metadata__contains='image'):
                data.append({
                    'project_name':     project_obj.id,
                    'label':            record.label,
                    'main_file':        record.main_file,
                    'repos_url':        record.repository.url,
                    'version':          record.version,
                    'reason':           record.reason,
                    'outcome':          record.outcome,
                    'tags':             tags,
                    'datastore_id':     data_key.output_from_record.datastore.id,
                    'path':             data_key.path,
                    'creation':         data_key.creation.strftime('%Y-%m-%d %H:%M:%S'),
                    'digest':           data_key.digest
                })
        if limit != -1:
            return HttpResponse(json.dumps(data[offset:offset+limit]), content_type='application/json')
        else:
            return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        tags = Tag.objects.all()
        return render(request, 'image_thumbgrid.html', {'project':project_obj, 'tags':tags})


def parameter_list(request, project):
    project_obj = Project.objects.get(id=project)
    main_file = request.GET.get('main_file', None)
    if main_file:
        record_list = Record.objects.filter(project_id=project, main_file=main_file)
        keys = []
        for record in record_list:
            try:
                parameter_set = record.parameters.to_sumatra()
                if hasattr(parameter_set, "as_dict"):
                    parameter_set = parameter_set.as_dict()
                parameter_set = parameters.nesteddictflatten(parameter_set)
                for key in parameter_set.keys():            # only works with simple parameter set
                    if key not in keys:
                        keys.append(key)
                keys.sort()
            except:
                return Http404
        return render(request, 'parameter_list.html',{'project':project_obj, 'object_list':record_list, 'keys': keys, 'main_file':main_file})
    else:
        return render(request, 'parameter_list.html',{'project':project_obj})


def delete_records(request, project):
    if django_settings.READ_ONLY:
        return HttpResponse('It is in read-only mode.')
    records_to_delete = request.POST.getlist('delete[]')
    delete_data = request.POST.get('delete_data', False)
    if isinstance(delete_data, str):
        # Convert strings returned from Javascript function into Python bools
        delete_data = {'false': False, 'true': True}[delete_data]
    records = Record.objects.filter(label__in=records_to_delete, project__id=project)
    if records:
        for record in records:
            if delete_data:
                datastore = record.datastore.to_sumatra()
                datastore.delete(*[data_key.to_sumatra()
                                   for data_key in record.output_data.all()])
            record.delete()
    return HttpResponse('OK')


def show_content(request, datastore_id):
    datastore = Datastore.objects.get(pk=datastore_id).to_sumatra()
    attrs = dict(path=request.GET['path'],
                 digest=request.GET['digest'],
                 creation=datestring_to_datetime(request.GET['creation']))
    data_key = DataKey.objects.get(**attrs).to_sumatra()
    mimetype = data_key.metadata["mimetype"]
    try:
        content = datastore.get_content(data_key)
    except (IOError, KeyError):
        raise Http404
    return HttpResponse(content, content_type=mimetype or "application/unknown")


def show_script(request, project, label):
    """ get the script content from the repos """
    record = Record.objects.get(label=label, project__id=project)
    file_content = record.to_sumatra().script_content
    if not file_content:
        raise Http404
    return HttpResponse('<p><span style="font-size: 16px; font-weight:bold">'+record.main_file+'</span><br><span>'+record.version+'</span></p><hr>'+file_content.replace(' ','&#160;').replace('\n', '<br />'))


def compare_records(request, project):
    record_labels = [request.GET['a'], request.GET['b']]
    db_records = Record.objects.filter(label__in=record_labels, project__id=project)
    records = [r.to_sumatra() for r in db_records]
    diff = RecordDifference(*records)
    context = {'db_records': db_records,
               'diff': diff,
               'project': Project.objects.get(pk=project)}
    if diff.input_data_differ:
        context['input_data_pairs'] = pair_datafiles(diff.recordA.input_data, diff.recordB.input_data)
    if diff.output_data_differ:
        context['output_data_pairs'] = pair_datafiles(diff.recordA.output_data, diff.recordB.output_data)
    return render(request, "record_comparison.html", context)



def pair_datafiles(data_keys_a, data_keys_b, threshold=0.7):
    import difflib
    from os.path import basename
    from copy import copy

    unmatched_files_a = copy(data_keys_a)
    unmatched_files_b = copy(data_keys_b)
    matches = []
    while unmatched_files_a and unmatched_files_b:
        similarity = []
        n2 = len(unmatched_files_b)
        for x in unmatched_files_a:
            for y in unmatched_files_b:
                # should check mimetypes. Different mime-type --> similarity set to 0
                similarity.append(
                    difflib.SequenceMatcher(a=basename(x.path),
                                            b=basename(y.path)).ratio())
        s_max = max(similarity)
        if s_max > threshold:
            i_max = similarity.index(s_max)
            matches.append((
                unmatched_files_a.pop(i_max%n2),
                unmatched_files_b.pop(i_max//n2)))
        else:
            break
    return {"matches": matches,
            "unmatched_a": unmatched_files_a,
            "unmatched_b": unmatched_files_b}


class SettingsView(View):

    def get(self, request):
        return HttpResponse(json.dumps(self.load_settings()), content_type='application/json')

    def post(self, request):
        if django_settings.READ_ONLY:
            return HttpResponse('It is in read-only mode.')
        settings = self.load_settings()
        data = json.loads(request.body.decode('utf-8'))
        settings.update(data["settings"])
        self.save_settings(settings)
        return HttpResponse('OK')

    def load_settings(self):
        if os.path.exists(global_conf_file):
            with open(global_conf_file, 'r') as fp:
                settings = json.load(fp)
        else:
            settings = {
                "hidden_cols": []
            }
        return settings

    def save_settings(self, settings):
        with open(global_conf_file, 'w') as fp:
            json.dump(settings, fp)


class DiffView(TemplateView):
    template_name = 'diff_view.html'

    def get_context_data(self, **kwargs):
        context = super(DiffView, self).get_context_data(**kwargs)
        project = self.kwargs["project"]
        label = unescape(self.kwargs["label"])
        package = self.kwargs.get("package", None)
        record = Record.objects.get(label=label, project__id=project)
        if package:
            dependency = record.dependencies.get(name=package)
        else:
            package = "Main script"
            dependency = record
        context.update({'label': label,
                        'project_name': project,
                        'package': package,
                        'parent_version': dependency.version,
                        'diff': dependency.diff})
        return context


#
# Ajax request for datatable
#

def datatable_record(request, project):
    columns = ['label', 'timestamp', 'reason', 'outcome', 'input_data', 'output_data',
     'duration', 'launch_mode', 'executable', 'main_file', 'version', 'script_arguments', 'tags']
    selected_tag = request.GET['tag']
    search_value = request.GET['search[value]']
    order = int(request.GET['order[0][column]'])
    order_dir = {'desc': '-', 'asc': ''}[request.GET['order[0][dir]']]
    length = int(request.GET['length'])
    start = int(request.GET['start'])
    draw = int(request.GET['draw'])

    records = Record.objects.filter(project__id=project)
    recordsTotal = len(records)

    # Filter by tag
    if selected_tag != '':
        records = records.filter(tags__contains=selected_tag)

    # Filter by search queries
    if search_value != '':
        search_queries = search_value.split(' ')
        for sq in search_queries:
            records = records.filter(
                Q(label__contains=sq) |
                Q(timestamp__contains=sq) |
                Q(reason__contains=sq) |
                Q(outcome__contains=sq) |
                Q(duration__contains=sq) |
                Q(main_file__contains=sq) |
                Q(version__contains=sq) |
                Q(tags__contains=sq)
                )
    records = records.order_by(order_dir+columns[order])                        # Ordering

    data = []
    for rec in records[start:start+length]:
        try:
            data.append({
                'DT_RowId':     rec.label,
                'project':      project,
                'label':        rec.label,
                'date':         rec.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'reason':       rec.reason,
                'outcome':      rec.outcome,
                'input_data':   map(lambda x: {'path': x.path, 'digest': x.digest, 'creation': x.creation.strftime('%Y-%m-%dT%H:%M:%S')}, rec.input_data.all()),
                'output_data':  map(lambda x: {'path': x.path, 'digest': x.digest, 'creation': x.creation.strftime('%Y-%m-%dT%H:%M:%S')}, rec.output_data.all()),
                'duration':     rec.duration,
                'processes':    rec.launch_mode.get_parameters().get('n',1),
                'executable':   '%s %s' %(rec.executable.name,rec.executable.version),
                'main_file':    rec.main_file,
                'diff' :        rec.diff,
                'version':      rec.version,
                'arguments':    rec.script_arguments,
                'tags':         [tag.name for tag in rec.tag_objects()],
            })
        except:
            pass

    response_json = json.dumps({
        "draw": draw,
        "recordsTotal": recordsTotal,
        "recordsFiltered": len(records),
        "data": data
        })

    return HttpResponse(response_json,content_type="application/json")


def datatable_data(request, project):
    columns = ['path', 'path', 'digest', 'metadata', 'creation', 'output_from_record','input_to_records']
    search_value = request.GET['search[value]']
    order = int(request.GET['order[0][column]'])
    order_dir = {'desc': '-', 'asc': ''}[request.GET['order[0][dir]']]
    length = int(request.GET['length'])
    start = int(request.GET['start'])
    draw = int(request.GET['draw'])

    datakeys = DataKey.objects.filter(output_from_record__project_id=project)
    datakeysTotal = len(datakeys)

    # Filter by search queries
    if search_value != '':
        search_queries = search_value.split(' ')
        for sq in search_queries:
            datakeys = datakeys.filter(
                Q(path__contains=sq) |
                Q(digest__contains=sq) |
                Q(creation__contains=sq) |
                Q(metadata__contains=sq)
                )
    datakeys = datakeys.order_by(order_dir+columns[order])                        # Ordering

    data = []
    for dk in datakeys[start:start+length]:
        try:
            data.append({
                'DT_RowId':             dk.path,
                'project':              project,
                'path':                 dk.path,
                'directory':            os.path.dirname(dk.path),
                'filename':             os.path.basename(dk.path),
                'digest':               dk.digest,
                'size':                 dk.get_metadata()['size'],
                # 'size':                 filters.filesizeformat(dk.get_metadata()['size']),
                'creation':             dk.creation.strftime('%Y-%m-%d %H:%M:%S'),
                'output_from_record':   dk.output_from_record.label,
                'input_to_records':     map(lambda x: x.label, dk.input_to_records.all())
            })
        except:
            pass

    response_json = json.dumps({
        "draw": draw,
        "recordsTotal": datakeysTotal,
        "recordsFiltered": len(datakeys),
        "data": data
        })

    return HttpResponse(response_json,content_type="application/json")


def datatable_image(request, project):
    columns = ['path','creation',
        'output_from_record__label', 'output_from_record__reason',
        'output_from_record__outcome', 'output_from_record__tags']
    selected_tag = request.GET['tag']
    search_value = request.GET['search[value]']
    order = int(request.GET['order[0][column]'])
    order_dir = {'desc': '-', 'asc': ''}[request.GET['order[0][dir]']]
    length = int(request.GET['length'])
    start = int(request.GET['start'])
    draw = int(request.GET['draw'])

    images = DataKey.objects.filter(output_from_record__project_id=project, metadata__contains='image')
    imagesTotal = len(images)

    # Filter by tag
    if selected_tag != '':
        images = images.filter(output_from_record__tags__contains=selected_tag)

    # Filter by search queries
    if search_value != '':
        search_queries = search_value.split(' ')
        for sq in search_queries:
            images = images.filter(
                Q(path__contains=sq) |
                Q(digest__contains=sq) |
                Q(creation__contains=sq) |
                Q(output_from_record__label__contains=sq) |
                Q(output_from_record__reason__contains=sq) |
                Q(output_from_record__outcome__contains=sq) |
                Q(output_from_record__tags__contains=sq)
                )
    images = images.order_by(order_dir+columns[order])                        # Ordering

    data = []
    for im in images[start:start+length]:
        try:
            data.append({
                'DT_RowId':     im.path,
                'project':      project,
                'date':         im.creation.strftime('%Y-%m-%d %H:%M:%S'),
                'creation':     im.creation.strftime('%Y-%m-%dT%H:%M:%S'),
                'path':         im.path,
                'digest':       im.digest,
                'datastore':    im.output_from_record.datastore.id,
                'record':       im.output_from_record.label,
                'reason':       im.output_from_record.reason,
                'outcome':      im.output_from_record.outcome,
                'parameters':   im.output_from_record.parameters.content.split('\n'),
                'tags':         [tag.name for tag in im.output_from_record.tag_objects()],
            })
        except:
            pass

    response_json = json.dumps({
        "draw": draw,
        "recordsTotal": imagesTotal,
        "recordsFiltered": len(images),
        "data": data
        })

    return HttpResponse(response_json,content_type="application/json")
