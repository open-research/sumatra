"""

:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input, edit_string_for_tags
from django.utils.safestring import mark_safe
try:
    from django.utils.encoding import force_bytes, force_text  # Django 1.5
except ImportError:
    from django.utils.encoding import smart_str as force_bytes, force_unicode as force_text  # Django 1.4
from os import name
from sumatra.formatting import human_readable_duration

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
