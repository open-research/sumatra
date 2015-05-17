"""

:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from __future__ import unicode_literals

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input
from django.utils.safestring import mark_safe
try:
    from django.utils.encoding import force_bytes, force_text  # Django 1.5
except ImportError:
    from django.utils.encoding import smart_str as force_bytes, force_unicode as force_text  # Django 1.4
from os import name, path
from sumatra.formatting import human_readable_duration
import json
import datetime

register = template.Library()


@register.filter
@stringfilter
def cut(text, type):
    if type == 'repo':
        if name == 'posix':
            text_out = text.split('/')[-1]
        else:
            text_out = text.split('\\')[-1]  # for windows
    elif type == 'vers':
        text_out = text[:5]
    return mark_safe(text_out)


@register.filter
@stringfilter
def ubreak(text):
    text_out = text.replace("_", "_<wbr>").replace("/","/<wbr>")
    return mark_safe(text_out)

@register.filter
@stringfilter
def basename(text):
    return mark_safe(path.basename(text))

# # DOES NOT WORK BECAUSE OF datetime.date
# import ast
# # dictionary lookup as suggested by stackoverflow.com/a/8000091/692634
# @register.filter
# def get_item(dictionary, key):
#     dictionary = ast.literal_eval(dictionary)
#     print dictionary[key]
#     return mark_safe(str(dictionary.get(key)))


@register.filter
def eval_metadata(data, key):
    '''Convert DataKey metadata from unicode to dicitionary and return
    item accessed by key.
    '''
    return data.get_metadata().get(key)

@register.filter
def parse_datetime(date):
    '''Parse float as datetime objects.'''
    if type(date) == float:
        #print date, type(date), datetime.datetime.fromtimestamp(date)
        return datetime.datetime.fromtimestamp(date)
    else:
        return date



@register.filter
def as_json(data):
    return mark_safe(json.dumps(data))


@register.filter
@stringfilter
def link(text, url):
    tags = parse_tag_input(text)
    template = '<a href="%s">%%s</a>' % url
    return mark_safe(" ".join(template % (tag, tag) for tag in tags))


@register.filter
@stringfilter
def escapeslash(text):
    return mark_safe(text.replace("/", "||"))


human_readable_duration = register.filter(human_readable_duration)

# copied from django.contrib.markup


@register.filter(is_safe=True)
def restructuredtext(value):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in 'restructuredtext' filter: The Python docutils library isn't installed.")
        return force_text(value)
    else:
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1", settings_overrides=docutils_settings)
        return mark_safe(force_text(parts["fragment"]))

