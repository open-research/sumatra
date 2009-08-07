from django.db import models

class SimulationGroup(models.Model):
    id = models.CharField(max_length=100, primary_key=True)

class Executable(models.Model):
    path = models.CharField(max_length=200)
    name = models.CharField(max_length=50)
    version = models.CharField(max_length=20)

class Script(models.Model):
    repository = models.URLField(verify_exists=False)
    main_file = models.CharField(max_length=50)

#class ParameterSet(models.Model):
#    pass

class LaunchMode(models.Model):
    type = models.CharField(max_length=10)
    parameters = models.CharField(max_length=100)

class Datastore(models.Model):
    type = models.CharField(max_length=30)
    parameters = models.CharField(max_length=100)

class SimulationRecord(models.Model):
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
    
    