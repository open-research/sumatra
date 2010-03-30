"""
Definition of database tables and object retrieval for the DjangoRecordStore.
"""

from django.db import models
from sumatra import programs, launch, datastore, records, versioncontrol, parameters, dependency_finder
import os.path
import tagging.fields
from tagging.models import Tag

class SumatraObjectsManager(models.Manager):
    
    def get_or_create_from_sumatra_object(self, obj):
        # automatically retrieving the field names is nice, but leads
        # to all the special cases below when we have subclasses that we
        # want to store in a single table in the database.
        # might be better to specify the list of field names explicitly
        # as an argument to the Manager __init__().
        field_names = self.model._meta.get_all_field_names()
        field_names.remove('id')
        field_names.remove('simulationrecord')
        attributes = {}
        for name in field_names:
            try:
                attributes[name] = getattr(obj, name)
            except AttributeError:
                if name == 'parameters':
                    attributes[name] = str(obj.get_state())
                elif name == 'type':
                    attributes[name] = obj.__class__.__name__
                elif name == 'content':
                    attributes[name] = str(obj) # ParameterSet
                else:
                    raise
        return self.get_or_create(**attributes)            
        

class BaseModel(models.Model):
    objects = SumatraObjectsManager()
    
    class Meta:
        abstract = True
    
    def field_names(self):
        field_names = self._meta.get_all_field_names()
        field_names.remove('id')
        field_names.remove('simulationrecord')
        return field_names
    

class SimulationGroup(BaseModel):
    id = models.CharField(max_length=100, primary_key=True)


class Executable(BaseModel):
    path = models.CharField(max_length=200)
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20)

    def to_sumatra(self):
        cls = programs.registered_program_names.get(self.name, programs.Executable)
        ex = cls(self.path, self.version)
        ex.name = self.name
        return ex


class Dependency(BaseModel):
    name = models.CharField(max_length=50)
    path = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    diff = models.TextField(blank=True)
    module = models.CharField(max_length=50)
    
    def __unicode__(self):
        return "%s (%s) version=%s" % (self.name, self.path, self.version)
    
    def to_sumatra(self):
        dep = getattr(dependency_finder, self.module).Dependency(self.name, self.path, self.version)
        if self.diff:
            dep.diff = self.diff
        return dep
        
    class Meta:
        ordering = ['name']


class Repository(BaseModel):
    # the following should be unique together.
    type = models.CharField(max_length=20)
    url = models.URLField(verify_exists=False)
    
    def to_sumatra(self):
        for m in versioncontrol.vcs_list:
            if hasattr(m, self.type):
                return getattr(m, self.type)(self.url)
        raise Exception("Repository type %s not supported." % self.type)


class ParameterSet(BaseModel):
    type = models.CharField(max_length=30)
    content = models.TextField()
    
    def to_sumatra(self):
        if hasattr(parameters, self.type):
            ps = getattr(parameters, self.type)(self.content)
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


class SimulationRecord(BaseModel):
    id = models.CharField(max_length=100, unique=True)
    db_id = models.AutoField(primary_key=True) # django-tagging needs an integer as primary key - see http://code.google.com/p/django-tagging/issues/detail?id=15
    group = models.ForeignKey(SimulationGroup)
    reason = models.TextField(blank=True)
    duration = models.FloatField(null=True)
    executable = models.ForeignKey(Executable)
    repository = models.ForeignKey(Repository)
    main_file = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    parameters = models.ForeignKey(ParameterSet)
    launch_mode = models.ForeignKey(LaunchMode)
    datastore = models.ForeignKey(Datastore)
    outcome = models.TextField(blank=True)
    data_key = models.TextField(blank=True)
    timestamp = models.DateTimeField()
    tags = tagging.fields.TagField()
    dependencies = models.ManyToManyField(Dependency)
    platforms = models.ManyToManyField(PlatformInformation)
    diff = models.TextField(blank=True)

    def to_sumatra(self):
        record = records.SimRecord(
            self.executable.to_sumatra(),
            self.repository.to_sumatra(),
            self.main_file,
            self.version,
            self.parameters.to_sumatra(),
            self.launch_mode.to_sumatra(),
            self.datastore.to_sumatra(),
            self.group.id,
            self.reason,
            self.diff)
        record.duration = self.duration
        record.outcome = self.outcome
        record.data_key = eval(self.data_key)
        record.timestamp = self.timestamp
        record.tags = set(tag.name for tag in Tag.objects.get_for_object(self))
        record.dependencies = [dep.to_sumatra() for dep in self.dependencies.all()]
        record.platforms = [pi.to_sumatra() for pi in self.platforms.all()]
        return record
            
    def __unicode__(self):
        return self.id
    
