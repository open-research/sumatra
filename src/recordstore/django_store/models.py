from django.db import models
from sumatra import programs, launch, datastore, records, versioncontrol

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
        print "field_names = ", field_names
        for name in field_names:
            try:
                attributes[name] = getattr(obj, name)
            except AttributeError:
                if name == 'parameters':
                    attributes[name] = str(obj.get_state())
                elif name == 'type':
                    attributes[name] = obj.__class__.__name__
                else:
                    raise
        return self.get_or_create(**attributes)            
        

class BaseModel(models.Model):
    objects = SumatraObjectsManager()
    
    class Meta:
        abstract = True
        

class SimulationGroup(BaseModel):
    id = models.CharField(max_length=100, primary_key=True)

class Executable(BaseModel):
    path = models.CharField(max_length=200)
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20)

    def to_sumatra(self):
        # need to deal with subclasses
        ex = programs.Executable(self.path, self.version)
        ex.name = self.name
        return ex

class Script(BaseModel):
    repository_type = models.CharField(max_length=20)
    repository_url = models.URLField(verify_exists=False)
    main_file = models.CharField(max_length=50)
    version = models.CharField(max_length=20)

    def to_sumatra(self):
        sc = programs.Script(repository_url=self.repository_url,
                             main_file=self.main_file)
        if sc.repository.__class__.__name__ != self.repository_type:
            for m in versioncontrol.vcs_list:
                if hasattr(m, self.repository_type):
                    sc.repository = getattr(m, self.repository_type)(self.repository_url)
                    break
        sc.version = self.version
        return sc

#class ParameterSet(BaseModel):
#    pass

class LaunchMode(BaseModel):
    type = models.CharField(max_length=10)
    parameters = models.CharField(max_length=100)
    
    def to_sumatra(self):
        if hasattr(launch, self.type):
            lm = getattr(launch, self.type)()
        else:
            raise Exception("Unknown launch mode '%s' stored in database" % self.type)
        return lm
    

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


class SimulationRecord(BaseModel):
    id = models.CharField(max_length=100, primary_key=True)
    group = models.ForeignKey(SimulationGroup)
    reason = models.TextField(blank=True)
    duration = models.FloatField(null=True)
    executable = models.ForeignKey(Executable)
    script = models.ForeignKey(Script)
    #parameters = models.ForeignKey(ParameterSet)
    launch_mode = models.ForeignKey(LaunchMode)
    datastore = models.ForeignKey(Datastore)
    outcome = models.TextField(blank=True)
    data_key = models.TextField(blank=True)
    timestamp = models.DateTimeField()

    def to_sumatra(self):
        record = records.SimRecord(
            self.executable.to_sumatra(),
            self.script.to_sumatra(),
            {}, # temporary
            self.launch_mode.to_sumatra(),
            self.datastore.to_sumatra(),
            self.group.id,
            self.reason)
        record.duration = self.duration
        record.outcome = self.outcome
        record.data_key = self.data_key
        record.timestamp = self.timestamp
        return record
            
            
    