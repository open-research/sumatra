"""
Handles storage of simulation/analysis records in a relational database, via the
Django object-relational mapper (ORM), which means that any database
supported by Django could in principle be used, although for now we assume
SQLite.
"""


from sumatra.recordstore.base import RecordStore
from sumatra.recordstore import serialization
import django.conf as django_conf
from django.core import management
import os
from textwrap import dedent
import imp

# Check that django-tagging is available. It would be better to try importing
# it, but that seems to mess with Django's internals.
imp.find_module("tagging")

class DjangoConfiguration(object):
    """
    To allow more than one DjangoRecordStore instances to exist at the same
    time, this class allows the database configuration to be built up in several
    steps, only actually doing the Django configuration step at the last
    possible moment.
    """
   
    def __init__(self):
        self._settings = {
            'DEBUG': True,
            'DATABASES': {},
            'INSTALLED_APPS': ('sumatra.recordstore.django_store',
                               'django.contrib.contenttypes', # needed for tagging
                               'tagging'),
        }
        self._n_databases = 0
        self.configured = False
   
    def add_database(self, db_file):
        """
        Add a database to the configuration and return a label. If the database
        already exists in the configuration, just return the existing label.
        """
        db_file = os.path.abspath(db_file)
        if self.contains_database(db_file):
            for key, db in self._settings['DATABASES'].items():
                if db_file == db['NAME']:
                    label = key
                    break
        else:
            if self.configured:
                raise Exception("Django already configured: you cannot create any more DjangoRecordStores. You must create all stores before using any of them.")
            if self._n_databases == 0:
                label = 'default'
            else:
                label = 'database%g' % self._n_databases
            self._settings['DATABASES'][label] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.abspath(db_file)
            }
            self._n_databases += 1
        return label
    
    def contains_database(self, db_file):
        return os.path.abspath(db_file) in self.get_db_files()
    
    def get_db_files(self):
        return [D['NAME'] for D in self._settings['DATABASES'].values()]

    def _create_databases(self):
        for label, db in self._settings['DATABASES'].items():
            db_file = db['NAME']
            if not os.path.exists(os.path.dirname(db_file)):
                os.makedirs(os.path.dirname(db_file))
            if not os.path.exists(db_file):
                management.call_command('syncdb', database=label, verbosity=1)

    def configure(self):
        settings = django_conf.settings
        if not settings.configured:
            settings.configure(**self._settings)
            management.setup_environ(settings)
            if not self.configured:
                self._create_databases()
            self.configured = True

db_config = DjangoConfiguration()


class DjangoRecordStore(RecordStore):
    
    def __init__(self, db_file='.smt/records'):    
        self._db_label = db_config.add_database(db_file)
        self._db_file = db_file
                
    def __str__(self):
        return "Relational database record store using the Django ORM (database file=%s)" % self._db_file
        
    def __getstate__(self):
        return {'db_file': self._db_file}
    
    def __setstate__(self, state):
        self._db_file = state['db_file']
        try:
            self._db_label = db_config.add_database(self._db_file)
        except:
            pass
        
    
    def _get_models(self):
        if not db_config.configured:
            db_config.configure()
        import models
        return models
    
    def _switch_db(self, db_file):
        # for testing
        global db_config
        settings = django_conf.settings
        settings._wrapped = None
        assert settings.configured == False
        db_config = DjangoConfiguration()
        if db_file:
            self.__init__(db_file)
    
    @property
    def _manager(self):
        models = self._get_models()
        return models.Record.objects.using(self._db_label)
    
    def _get_db_record(self, project_name, record):
        models = self._get_models()
        db_project = self._get_db_project(project_name)
        try:
            db_record = self._manager.get(label=record.label, project=db_project)
        except models.Record.DoesNotExist:
            db_record = models.Record(label=record.label, project=db_project)
            db_record._state.db = self._db_label
        return db_record
    
    def _get_db_project(self, project_name):
        models = self._get_models()
        try:
            db_project = models.Project.objects.using(self._db_label).get(id=project_name)
        except models.Project.DoesNotExist:
            db_project = models.Project(id=project_name)
            db_project.save()
        return db_project

    def _get_db_obj(self, db_class, obj):
        models = self._get_models()
        cls = getattr(models, db_class)
        db_obj, created = cls.objects.get_or_create_from_sumatra_object(obj, using=self._db_label)
        if created:
            db_obj.save(using=self._db_label)
        return db_obj        
    
    def list_projects(self):
        models = self._get_models()
        return [project.id for project in models.Project.objects.using(self._db_label).all()]
    
    def save(self, project_name, record):
        db_record = self._get_db_record(project_name, record)
        for attr in 'reason', 'duration', 'outcome', 'main_file', 'version', 'timestamp':
            value = getattr(record, attr)
            if value is not None:
                setattr(db_record, attr, value)
        db_record.executable = self._get_db_obj('Executable', record.executable)
        db_record.repository = self._get_db_obj('Repository', record.repository)
        db_record.launch_mode = self._get_db_obj('LaunchMode', record.launch_mode)
        db_record.datastore = self._get_db_obj('Datastore', record.datastore)
        db_record.parameters = self._get_db_obj('ParameterSet', record.parameters)
        db_record.script_arguments = record.script_arguments
        db_record.user = record.user
        db_record.tags = ",".join(record.tags)
        db_record.stdout_stderr = "\n".join(record.stdout_stderr)
        # should perhaps check here for any orphan Tags, i.e., those that are no longer associated with any records, and delete them
        db_record.save() # need to save before using many-to-many relationship
        for key in record.input_data:
            db_record.input_data.add(self._get_db_obj('DataKey', key))
        for key in record.output_data:
            db_record.output_data.add(self._get_db_obj('DataKey', key))
        for dep in record.dependencies:
            #print "Adding dependency %s to db_record" % dep
            db_record.dependencies.add(self._get_db_obj('Dependency', dep))
        for pi in record.platforms:
            db_record.platforms.add(self._get_db_obj('PlatformInformation', pi))
        db_record.diff = record.diff
        db_record.save(using=self._db_label)
        
    def get(self, project_name, label):
        models = self._get_models()
        try:
            db_record = self._manager.get(project__id=project_name, label=label)
        except models.Record.DoesNotExist:
            raise KeyError(label)
        return db_record.to_sumatra()
    
    def list(self, project_name, tags=None):
        db_records = self._manager.filter(project__id=project_name)
        if tags:
            if not hasattr(tags, "__len__"):
                tags = [tags]
            for tag in tags:
                db_records = db_records.filter(tags__contains=tag)
        try:
            records = [db_record.to_sumatra() for db_record in db_records]
        except Exception, err:
            errmsg = dedent("""\
                Sumatra could not retrieve the record from the record store.
                Possibly your record store was created with an older version of Sumatra.
                Please see http://packages.python.org/Sumatra/upgrading.html for information on upgrading.
                The original error message was: '%s: %s'""" % (err.__class__.__name__, err))
            raise Exception(errmsg)
        return records

    def labels(self, project_name):
        return [record.label for record in self._manager.filter(project__id=project_name)]
    
    def delete(self, project_name, label):
        db_record = self._manager.get(label=label, project__id=project_name)
        db_record.delete()
        
    def delete_by_tag(self, project_name, tag):
        db_records = self._manager.filter(project__id=project_name, tags__contains=tag)
        n = db_records.count()
        for db_record in db_records:
            db_record.delete()
        return n
    
    def most_recent(self, project_name):
        models = self._get_models()
        return self._manager.filter(project__id=project_name).latest('timestamp').label
    
    def delete_all(self):
        """Delete everything from the database."""
        management.call_command('flush', database=self._db_label,
                                interactive=False, verbosity=0)
    
    def _dump(self, indent=2):
        """
        Dump the database contents to a JSON-encoded string
        """
        import sys, StringIO
        data = StringIO.StringIO()
        sys.stdout = data
        management.call_command('dumpdata', 'django_store', 'tagging', indent=indent)
        sys.stdout = sys.__stdout__
        data.seek(0)
        return data.read()
