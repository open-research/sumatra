from django import template
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input, edit_string_for_tags
from django.utils.safestring import mark_safe

register = template.Library()

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