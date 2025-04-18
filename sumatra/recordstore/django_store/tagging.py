# The following models and managers are taken from django-tagging
# Specifically from the following fork and commit:
# - https://github.com/jazzband/django-tagging/commit/79cb321b1e4c464d39ed96ddbef02617ab0c692e


from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_str
from django.db import connection
from django.db.models.query_utils import Q
from django.db.models import signals
from django.db.models.fields import CharField

from .tagging_utils import (parse_tag_input, edit_string_for_tags)

qn = connection.ops.quote_name


class TagField(CharField):
    """
    A "special" character field that actually works as a relationship to tags
    "under the hood". This exposes a space-separated string of tags, but does
    the splitting/reordering/etc. under the hood.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)
        kwargs['blank'] = kwargs.get('blank', True)
        super(TagField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(TagField, self).contribute_to_class(cls, name)

        # Make this object the descriptor for field access.
        setattr(cls, self.name, self)

        # Save tags back to the database post-save
        signals.post_save.connect(self._save, cls, True)

    def __get__(self, instance, owner=None):
        """
        Tag getter. Returns an instance's tags if accessed on an instance, and
        all of a model's tags if called on a class. That is, this model::

           class Link(models.Model):
               ...
               tags = TagField()

        Lets you do both of these::

           >>> l = Link.objects.get(...)
           >>> l.tags
           'tag1 tag2 tag3'

           >>> Link.tags
           'tag1 tag2 tag3 tag4'

        """
        # Handle access on the model (i.e. Link.tags)
        if instance is None:
            return edit_string_for_tags(Tag.objects.usage_for_model(owner))

        tags = self._get_instance_tag_cache(instance)
        if tags is None:
            if instance.pk is None:
                self._set_instance_tag_cache(instance, '')
            else:
                self._set_instance_tag_cache(
                    instance, edit_string_for_tags(
                        Tag.objects.get_for_object(instance)))
        return self._get_instance_tag_cache(instance)

    def __set__(self, instance, value):
        """
        Set an object's tags.
        """
        if instance is None:
            raise AttributeError(
                '%s can only be set on instances.' % self.name)
        self._set_instance_tag_cache(instance, value)

    def _save(self, **kwargs):  # signal, sender, instance):
        """
        Save tags back to the database
        """
        tags = self._get_instance_tag_cache(kwargs['instance'])
        if tags is not None:
            Tag.objects.update_tags(kwargs['instance'], tags)

    def __delete__(self, instance):
        """
        Clear all of an object's tags.
        """
        self._set_instance_tag_cache(instance, '')

    def _get_instance_tag_cache(self, instance):
        """
        Helper: get an instance's tag cache.
        """
        return getattr(instance, '_%s_cache' % self.attname, None)

    def _set_instance_tag_cache(self, instance, tags):
        """
        Helper: set an instance's tag cache.
        """
        # The next instruction does nothing particular,
        # but needed to by-pass the deferred fields system
        # when saving an instance, which check the keys present
        # in instance.__dict__.
        # The issue is introducted in Django 1.10
        instance.__dict__[self.attname] = tags
        setattr(instance, '_%s_cache' % self.attname, tags)

    def get_internal_type(self):
        return 'CharField'


class TagManager(models.Manager):

    def update_tags(self, obj, tag_names):
        """
        Update tags associated with an object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        current_tags = list(self.filter(items__content_type__pk=ctype.pk,
                                        items__object_id=obj.pk))
        updated_tag_names = parse_tag_input(tag_names)

        # Remove tags which no longer apply
        tags_for_removal = [tag for tag in current_tags
                            if tag.name not in updated_tag_names]
        if len(tags_for_removal):
            TaggedItem._default_manager.filter(
                content_type__pk=ctype.pk,
                object_id=obj.pk,
                tag__in=tags_for_removal).delete()
        # Add new tags
        current_tag_names = [tag.name for tag in current_tags]
        for tag_name in updated_tag_names:
            if tag_name not in current_tag_names:
                tag, created = self.get_or_create(name=tag_name)
                TaggedItem._default_manager.get_or_create(
                    content_type_id=ctype.pk,
                    object_id=obj.pk,
                    tag=tag,
                )

    def get_for_object(self, obj):
        """
        Create a queryset matching all tags associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(items__content_type__pk=ctype.pk,
                           items__object_id=obj.pk)


class Tag(models.Model):
    """
    A tag.
    """
    name = models.CharField(
        'name', max_length=50,
        unique=True, db_index=True)

    objects = TagManager()

    class Meta:
        ordering = ('name',)
        verbose_name = 'tag'
        verbose_name_plural = 'tags'

    def __str__(self):
        return self.name


class TaggedItem(models.Model):
    """
    Holds the relationship between a tag and the item being tagged.
    """
    tag = models.ForeignKey(
        Tag,
        verbose_name='tag',
        related_name='items',
        on_delete=models.CASCADE)

    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content type',
        on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField(
        'object id',
        db_index=True)

    object = GenericForeignKey(
        'content_type', 'object_id')

    class Meta:
        # Enforce unique tag association per object
        unique_together = (('tag', 'content_type', 'object_id'),)
        verbose_name = 'tagged item'
        verbose_name_plural = 'tagged items'

    def __str__(self):
        return '%s [%s]' % (smart_str(self.object), smart_str(self.tag))
