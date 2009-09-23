from sumatra.recordstore import RecordStore
from django.conf import settings
from django.core import management
import os

recordstore_settings = {
    'DEBUG': True,
    'DATABASE_ENGINE': 'sqlite3',
    'INSTALLED_APPS': ('sumatra.recordstore.django_store',),
}

class DjangoRecordStore(RecordStore):
    
    def __init__(self, db_file='.smt/smt.db'):
        self._db_file = db_file
        recordstore_settings['DATABASE_NAME'] = db_file
        if not settings.configured:
            settings.configure(**recordstore_settings)
            management.setup_environ(settings)
            if not os.path.exists(os.path.dirname(db_file)):
                os.makedirs(os.path.dirname(db_file))
            if not os.path.exists(db_file):
                management.call_command('syncdb')
        else:
            assert settings.DATABASE_NAME == db_file
                
    def __str__(self):
        return "Relational database record store using the Django ORM (database file=%s)" % self._db_file
        
    def __getstate__(self):
        return self._db_file
    
    def __setstate__(self, state):
        self.__init__(state)
    
    def _get_db_group(self, group):
        import models
        db_group, created = models.SimulationGroup.objects.get_or_create(id=group)
        if created:
            db_group.save()
        return db_group
    
    def _get_db_record(self, record):
        import models
        db_group = self._get_db_group(record.group)
        try:
            db_record = models.SimulationRecord.objects.get(id=record.label,
                                                            group=db_group,
                                                            timestamp=record.timestamp)
        except models.SimulationRecord.DoesNotExist:
            db_record = models.SimulationRecord(id=record.label,
                                                group=db_group,
                                                timestamp=record.timestamp)
        return db_record
        
    def _get_db_script(self, script):
        db_script, created = models.Script.objects.get_or_create(repository_url=script.repository.url,
                                                                 repository_type=script.repository.__class__.__name__,
                                                                 main_file=script.main_file,
                                                                 version=script.version)
        if created:
            db_script.save()
        return db_script
                                                                     
    def _get_db_obj(self, db_class, obj):
        import models
        cls = getattr(models, db_class)
        db_obj, created = cls.objects.get_or_create_from_sumatra_object(obj)
        if created:
            db_obj.save()
        return db_obj        
    
    def save(self, record):
        db_record = self._get_db_record(record)
        for attr in 'reason', 'duration', 'outcome':
            value = getattr(record, attr)
            if value is not None:
                setattr(db_record, attr, value)
        db_record.data_key = str(record.data_key)
        db_record.executable = self._get_db_obj('Executable', record.executable)
        db_record.script = self._get_db_script(record.script)
        db_record.launch_mode = self._get_db_obj('LaunchMode', record.launch_mode)
        db_record.datastore = self._get_db_obj('Datastore', record.datastore)
        db_record.parameters = self._get_db_obj('ParameterSet', record.parameters)
        import django.db.models.manager
        def debug(f):
            def _debug(model, values, **kwargs):
                print "model = ", model
                print "values = ", values
                print "kwargs = ", kwargs
                return f(model, values, **kwargs)
            return _debug
        #django.db.models.manager.insert_query = debug(django.db.models.manager.insert_query)
        
        db_record.save()
        
    
    def get(self, label):
        import models
        db_record = models.SimulationRecord.objects.get(id=label)
        return db_record.to_sumatra()
    
    def list(self, groups):
        import models
        db_records = models.SimulationRecord.objects.all()
        if groups:
            db_records = db_records.filter(group__in=groups)
        return [db_record.to_sumatra() for db_record in db_records]
    
    def delete(self, label):
        import models
        db_record = models.SimulationRecord.objects.get(id=label)
        db_record.delete()
    
def test():
    djrs = DjangoRecordStore()
    import sumatra.records, sumatra.programs, sumatra.datastore, sumatra.launch
    from sumatra.versioncontrol.base import Repository
    ex = sumatra.programs.PythonExecutable('/usr/bin/python', '2.5')
    class MockScript(object): pass
    sc = MockScript()
    sc.repository = Repository("http://svn.example.com")
    sc.main_file = 'main_file.py'
    sc.version = '7a6b6cd5'
    lm = sumatra.launch.SerialLaunchMode()
    ds = sumatra.datastore.FileSystemDataStore('/dev/null')
    record = sumatra.records.SimRecord(ex, sc, {}, lm, ds, "aLabel", "aReason")
    record.outcome = "anOutcome"
    record.duration = 123.45
    djrs.save(record)
    print "\nSaved record:"
    print record.describe()
    record2 = djrs.get(record.label)
    print "\nRetrieved record:"
    print record2.describe()
    