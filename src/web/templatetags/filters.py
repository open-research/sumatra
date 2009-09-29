from django import template
from django.template.defaultfilters import stringfilter
from tagging.utils import parse_tag_input, edit_string_for_tags
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def link(text):
    tags = parse_tag_input(text)
    return mark_safe(" ".join('<a href="/tag/%s/">%s</a>' % (tag,tag) for tag in tags))
    
    
    
    
