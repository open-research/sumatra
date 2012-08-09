from django import template
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input, edit_string_for_tags
from django.utils.safestring import mark_safe
from math import modf
from os import name

register = template.Library()

@register.filter
@stringfilter
def cut(text, type):
    if type == 'repo':
        if name == 'posix':
            text_out = text.split('/')[-1]
        else:
            text_out = text.split('\\')[-1] # for windows
    elif type == 'vers':
        text_out = text[:5]
    return mark_safe(text_out)
    
@register.filter
@stringfilter
def link(text, url):
    tags = parse_tag_input(text)
    template = '<a href="%s">%%s</a>' % url
    return mark_safe(" ".join(template % (tag,tag) for tag in tags))
    
@register.filter
@stringfilter
def escapeslash(text):
    return mark_safe(text.replace("/","||"))


def _quotient_remainder(dividend, divisor):
    q = dividend // divisor
    r = dividend - q * divisor
    return (q, r)


@register.filter
def human_readable_duration(seconds):
    """
    Coverts seconds to human readable unit

    >>> human_readable_duration(((6 * 60 + 32) * 60 + 12))
    '6h 32m 12.00s'
    >>> human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60 + 5))
    '8d 7h 6m 5.00s'
    >>> human_readable_duration((((8 * 24 + 7) * 60 + 6) * 60))
    '8d 7h 6m'
    >>> human_readable_duration((((8 * 24 + 7) * 60) * 60))
    '8d 7h'
    >>> human_readable_duration((((8 * 24) * 60) * 60))
    '8d'
    >>> human_readable_duration((((8 * 24) * 60) * 60) + 0.12)
    '8d 0.12s'

    """
    (fractional_part, integer_part) = modf(seconds)
    (d, rem) = _quotient_remainder(int(integer_part), 60 * 60 * 24)
    (h, rem) = _quotient_remainder(rem, 60 * 60)
    (m, rem) = _quotient_remainder(rem, 60)
    s = rem + fractional_part
    
    return ' '.join(
        templ.format(val)
        for (val, templ) in [
            (d, '{0}d'),
            (h, '{0}h'),
            (m, '{0}m'),
            (s, '{0:.2f}s'),
            ]
        if val != 0
        )
