from sumatra.recordstore import RecordStore
from django.conf import settings
from django.core import management
import os.path

recordstore_settings = {
    'DEBUG': True,
    'DATABASE_ENGINE': 'sqlite3',
    'INSTALLED_APPS': ('sumatra.recordstore.django_store',),
}

class DjangoRecordStore(RecordStore):
    
    def __init__(self, db_file='.smt/smt.db'):
        self._db_file = db_file
        recordstore_settings['DATABASE_NAME'] = self._db_file
        settings.configure(**recordstore_settings)
        management.setup_environ(settings)
        if not os.path.exists(recordstore_settings['DATABASE_NAME']):
            management.call_command('syncdb')
                
    def __str__(self):
        return "Relational database record store using the Django ORM (database file=%s)" % self._db_file
        
    #def __getstate__(self):
    #    pass
    
    #def __setstate__(self, state):
    #    self.__init__(state)
    
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
        
    def _get_db_obj(self, db_class, obj):
        import models
        cls = getattr(models, db_class)
        # automatically retrieving the field names is nice, but leads
        # to all the special cases below when we have subclasses that we
        # want to store in a single table in the database.
        # might be better to specify the list of field names explicitly
        # as an argument.
        field_names = cls._meta.get_all_field_names()
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
                    attributes[name] = repr(obj)
                else:
                    raise
        print "object type = ", type(obj)
        db_obj, created = cls.objects.get_or_create(**attributes)
        if created:
            db_obj.save()
        return db_obj        
    
    def save(self, record):
        db_record = self._get_db_record(record)
        for attr in 'reason', 'duration', 'outcome', 'data_key':
            value = getattr(record, attr)
            if value is not None:
                setattr(db_record, attr, value)
        db_record.executable = self._get_db_obj('Executable', record.executable)
        db_record.script = self._get_db_obj('Script', record.script)
        db_record.launch_mode = self._get_db_obj('LaunchMode', record.launch_mode)
        db_record.datastore = self._get_db_obj('Datastore', record.datastore)
        db_record.save()
    
    def get(self, label):
        import models
        db_record = models.SimulationRecord.objects.get(id=label)
        
    
    def list(self, groups):
        raise NotImplememtedError
    
    def delete(self, label):
        raise NotImplememtedError
    
def test():
    djrs = DjangoRecordStore()
    import sumatra.records, sumatra.programs, sumatra.datastore, sumatra.launch
    ex = sumatra.programs.PythonExecutable('/usr/bin/python', '2.5')
    class MockScript(object): pass
    sc = MockScript()
    sc.repository = '/path/to/repos'
    sc.main_file = 'main_file.py'
    lm = sumatra.launch.SerialLaunchMode()
    ds = sumatra.datastore.FileSystemDataStore('/dev/null')
    record = sumatra.records.SimRecord(ex, sc, {}, lm, ds, "aLabel", "aReason")
    record.outcome = "anOutcome"
    record.duration = 123.45
    djrs.save(record)
    djrs.get(record)
    