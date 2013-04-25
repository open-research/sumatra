"""
Definition of database tables and object retrieval for the DjangoRecordStore.
"""

from django.db import models
from django.contrib.auth.models import User
from sumatra import programs, launch, datastore, records, versioncontrol, parameters, dependency_finder
import os.path
import tagging.fields
from tagging.models import Tag
from datetime import datetime
import django
from distutils.version import LooseVersion


class SumatraObjectsManager(models.Manager):
    
    def get_or_create_from_sumatra_object(self, obj, using='default'):
        # automatically retrieving the field names is nice, but leads
        # to all the special cases below when we have subclasses that we
        # want to store in a single table in the database.
        # might be better to specify the list of field names explicitly
        # as an argument to the Manager __init__().
        excluded_fields = ('id', 'record', 'input_to_records', 'output_from_records')
        field_names = set(self.model._meta.get_all_field_names()).difference(excluded_fields)
        attributes = {}
        for name in field_names:
            try:
                attributes[name] = getattr(obj, name)
            except AttributeError:
                if name == 'parameters':
                    attributes[name] = str(obj.__getstate__())
                elif name == 'type':
                    attributes[name] = obj.__class__.__name__
                elif name in ('content', 'metadata'):    
                    attributes[name] = str(obj) # ParameterSet, DataKey
                else:
                    raise
        return self.using(using).get_or_create(**attributes)            
        

class BaseModel(models.Model):
    objects = SumatraObjectsManager()
    
    class Meta:
        abstract = True
    
    def field_names(self):
        field_names = self._meta.get_all_field_names()
        field_names.remove('id')
        field_names.remove('record')
        return field_names
    

class Project(BaseModel):
    id = models.SlugField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('id',)

    def get_name(self):
        return self.name or self.id

    def __unicode__(self):
        return self.id
    
    def last_updated(self):
        return self.record_set.all().aggregate(models.Max('timestamp'))["timestamp__max"] or datetime(1970, 1, 1, 0, 0, 0)


class Executable(BaseModel):
    path = models.CharField(max_length=200)
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    options = models.CharField(max_length=50)

    def __unicode__(self):
        return self.path

    def to_sumatra(self):
        cls = programs.registered_program_names.get(self.name, programs.Executable)
        ex = cls(self.path, self.version, self.options)
        ex.name = self.name
        return ex


class Dependency(BaseModel):
    name = models.CharField(max_length=50)
    path = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    diff = models.TextField(blank=True)
    source = models.CharField(max_length=200, null=True, blank=True)
    module = models.CharField(max_length=50) # should be called language, or something
    
    def __unicode__(self):
        return "%s (%s) version=%s" % (self.name, self.path, self.version)
    
    def to_sumatra(self):
        return getattr(dependency_finder, self.module).Dependency(
                    self.name, self.path, self.version, self.diff, self.source)
        
    class Meta:
        ordering = ['name']


class Repository(BaseModel):
    # the following should be unique together.
    type = models.CharField(max_length=20)
    if LooseVersion(django.get_version()) < LooseVersion('1.5'):
        url = models.URLField(verify_exists=False)
        upstream = models.URLField(verify_exists=False, null=True, blank=True)
    else:
        url = models.URLField()
        upstream = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.url
    
    def to_sumatra(self):
        for m in versioncontrol.vcs_list:
            if hasattr(m, self.type):
                repos = getattr(m, self.type)(self.url)
                repos.upstream = self.upstream
                return repos
        raise Exception("Repository type %s not supported." % self.type)


class ParameterSet(BaseModel):
    type = models.CharField(max_length=30)
    content = models.TextField()
    
    def to_sumatra(self):
        if hasattr(parameters, self.type):
            ps = getattr(parameters, self.type)(self.content)
        elif self.content == u'None':
            ps = None
        elif self.content == u'{}':
            ps = {}
        else:
            ps = self.content
        return ps


class LaunchMode(BaseModel):
    type = models.CharField(max_length=10)
    parameters = models.CharField(max_length=100)
    
    def to_sumatra(self):
        parameters = eval(self.parameters)
        if hasattr(launch, self.type):
            lm = getattr(launch, self.type)(**parameters)
        else:
            raise Exception("Unknown launch mode '%s' stored in database" % self.type)
        return lm

    def get_parameters(self):
        return eval(self.parameters)
    

class Datastore(BaseModel):
    type = models.CharField(max_length=30)
    parameters = models.CharField(max_length=100)

    def to_sumatra(self):
        parameters = eval(self.parameters)
        if hasattr(datastore, self.type):
            ds = getattr(datastore, self.type)(**parameters)
        else:
            raise Exception("Unknown datastore type '%s' stored in database" % self.type)
        return ds

    def access_parameters(self):
        return eval(self.parameters)


class DataKey(BaseModel):
    path = models.CharField(max_length=200)
    digest = models.CharField(max_length=40)
    metadata = models.TextField(blank=True)
    
    class Meta:
        ordering = ('path',)

    def get_metadata(self):
        return eval(self.metadata) # should probably use json.decode
    
    def to_sumatra(self):
        metadata = eval(self.metadata)
        return datastore.DataKey(self.path, self.digest, **metadata)


class PlatformInformation(BaseModel):
    architecture_bits = models.CharField(max_length=10)
    architecture_linkage = models.CharField(max_length=10)
    machine = models.CharField(max_length=20)
    network_name = models.CharField(max_length=100)
    ip_addr = models.IPAddressField()
    processor = models.CharField(max_length=30)
    release = models.CharField(max_length=30)
    system_name = models.CharField(max_length=20)
    version = models.CharField(max_length=50)
    
    def to_sumatra(self):
        pi = {}
        for name in self.field_names():
            pi[name] = getattr(self, name)
        return launch.PlatformInformation(**pi)


class Record(BaseModel):
    label = models.CharField(max_length=100, unique=False) # make this a SlugField? samarkanov changed unique to False for the search form.
    db_id = models.AutoField(primary_key=True) # django-tagging needs an integer as primary key - see http://code.google.com/p/django-tagging/issues/detail?id=15
    reason = models.TextField(blank=True)
    duration = models.FloatField(null=True)
    executable = models.ForeignKey(Executable, null=True, blank=True) # null and blank for the search. If user doesn't want to specify the executable during the search
    repository = models.ForeignKey(Repository, null=True, blank=True) # null and blank for the search.
    main_file = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    parameters = models.ForeignKey(ParameterSet)
    input_data = models.ManyToManyField(DataKey, related_name="input_to_records")
    launch_mode = models.ForeignKey(LaunchMode)
    datastore = models.ForeignKey(Datastore)
    input_datastore = models.ForeignKey(Datastore, related_name="input_to_records")
    outcome = models.TextField(blank=True)
    timestamp = models.DateTimeField()
    tags = tagging.fields.TagField()
    output_data = models.ManyToManyField(DataKey, related_name="output_from_records")
    dependencies = models.ManyToManyField(Dependency)
    platforms = models.ManyToManyField(PlatformInformation)
    diff = models.TextField(blank=True)
    user = models.CharField(max_length=30)
    project = models.ForeignKey(Project, null=True)
    script_arguments = models.TextField(blank=True)
    stdout_stderr = models.TextField(blank=True)
    repeats = models.CharField(max_length=100, null=True, blank=True)

    # parameters which will be used in the fulltext search (see sumatra.web.services fulltext_search)
    params_search = ('label','reason', 'duration', 'main_file', 'outcome', 'user', 'tags') 

    class Meta:
        ordering = ('-timestamp',)

    def to_sumatra(self):
        record = records.Record(
            self.executable.to_sumatra(),
            self.repository.to_sumatra(),
            self.main_file,
            self.version,
            self.launch_mode.to_sumatra(),
            self.datastore.to_sumatra(),
            self.parameters.to_sumatra(),
            [key.to_sumatra() for key in self.input_data.all()],
            self.script_arguments,
            self.label,
            self.reason,
            self.diff,
            self.user,
            input_datastore=self.input_datastore.to_sumatra(),
            timestamp=self.timestamp)
        record.stdout_stderr = self.stdout_stderr
        record.duration = self.duration
        record.outcome = self.outcome
        record.tags = set(tag.name for tag in Tag.objects.get_for_object(self))
        record.output_data = [key.to_sumatra() for key in self.output_data.all()]
        record.dependencies = [dep.to_sumatra() for dep in self.dependencies.all()]
        record.platforms = [pi.to_sumatra() for pi in self.platforms.all()]
        record.repeats = self.repeats
        return record
            
    def __unicode__(self):
        return self.label
    
    def tag_objects(self):
        return Tag.objects.get_for_object(self) 

    def command_line(self):
        return self.to_sumatra().command_line
    
    def working_directory(self):
        return self.launch_mode.get_parameters().get('working_directory', None)
    
