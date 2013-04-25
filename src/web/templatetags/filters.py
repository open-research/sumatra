from django import template
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input, edit_string_for_tags
from django.utils.safestring import mark_safe
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


human_readable_duration = register.filter(human_readable_duration)
