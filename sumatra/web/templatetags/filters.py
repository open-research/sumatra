"""

:copyright: Copyright 2006-2015 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

import os
from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.safestring import mark_safe
try:
    from django.utils.encoding import force_bytes, force_text  # Django 1.5+
except ImportError:
    from django.utils.encoding import smart_str as force_bytes, force_unicode as force_text  # Django 1.4
from sumatra.formatting import human_readable_duration

register = template.Library()


@register.filter
@stringfilter
def ubreak(text):
    text_out = text.replace("_", "_<wbr>").replace("/", "/<wbr>")
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
        return force_text(value)
    else:
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1", settings_overrides=docutils_settings)
        return mark_safe(force_text(parts["fragment"]))
