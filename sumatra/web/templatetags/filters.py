"""

:copyright: Copyright 2006-2020, 2024 by the Sumatra team, see doc/authors.txt
:license: BSD 2-clause, see LICENSE for details.
"""

import os
from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_bytes, force_str
from sumatra.formatting import human_readable_duration
from sumatra.core import STATUS_PATTERN

register = template.Library()


@register.filter
@stringfilter
def ubreak(text):
    text_out = text.replace("_", "_<wbr>").replace("/", "/<wbr>")
    return mark_safe(text_out)

@register.filter
@stringfilter
def nbsp(text):
    text_out = text.replace(" ", "&nbsp;")
    return mark_safe(text_out)

@register.filter
@stringfilter
def basename(text):
    return mark_safe(os.path.basename(text))


@register.filter
@stringfilter
def dirname(text):
    return mark_safe(os.path.dirname(text))


@register.filter
def get_item(parameter_set, key):
    if hasattr(parameter_set, "as_dict"):
        parameter_set = parameter_set.as_dict()
    keys = key.split('.')
    for key in keys:
        if parameter_set:
            parameter_set = parameter_set.get(key)
    return parameter_set


@register.filter
def eval_metadata(data, key):
    '''Convert DataKey metadata from unicode to dictionary and return
    item accessed by key.
    '''
    return data.get_metadata().get(key)

human_readable_duration = register.filter(human_readable_duration)


@register.filter(is_safe=True)
def restructuredtext(value):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in 'restructuredtext' filter: The Python docutils library isn't installed.")
        return force_str(value)
    else:
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1", settings_overrides=docutils_settings)
        return mark_safe(force_str(parts["fragment"]))

@register.filter(needs_autoescape=True)
def labelize_tag(tag, autoescape=True):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    style_map = {
        'initialized': "default",
        'pre_run': "info",
        'running': "info",
        'finished': "primary",
        'failed': "danger",
        'killed': "warning",
        'succeeded': "success",
        'crashed': "danger"
    }
    m = STATUS_PATTERN.match(tag)
    if m:
        style = style_map[m.group(2)]
#         tag = m.group(1)
    else:
        style = "default"
    result = '<span class="label label-%s">%s</span>' % (style, esc(tag))
    return mark_safe(result)
