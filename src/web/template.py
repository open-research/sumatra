from django.template.loader_tags import BlockNode, ExtendsNode
from django.template import loader, Context, RequestContext, TextNode
from django.shortcuts import render_to_response

def get_template(template):
    if isinstance(template, (tuple, list)):
        return loader.select_template(template)
    return loader.get_template(template)

class BlockNotFound(Exception):
    pass

def render_template_block(template, block, context):
    """
    Renders a single block from a template. This template should have previously been rendered.
    """
    return render_template_block_nodelist(template.nodelist, block, context)
    
def render_template_block_nodelist(nodelist, block, context):
    for node in nodelist:
        if isinstance(node, BlockNode) and node.name == block:
            return node.render(context)
        for key in ('nodelist', 'nodelist_true', 'nodelist_false'):
            if hasattr(node, key):
                try:
                    return render_template_block_nodelist(getattr(node, key), block, context)
                except:
                    pass
    for node in nodelist:
        if isinstance(node, ExtendsNode):
            try:
                return render_template_block(node.get_parent(context), block, context)
            except BlockNotFound:
                pass
    raise BlockNotFound

def render_block_to_string(template_name, block, dictionary=None, context_instance=None):
    """
    Loads the given template_name and renders the given block with the given dictionary as
    context. Returns a string.
    """
    dictionary = dictionary or {}
    t = get_template(template_name)
    if context_instance:
        context_instance.update(dictionary)
    else:
        context_instance = Context(dictionary)
    t.render(context_instance)
    return render_template_block(t, block, context_instance)

def direct_block_to_template(request, template, block, extra_context=None, mimetype=None, **kwargs):
    """
    Render a given block in a given template with any extra URL parameters in the context as
    ``{{ params }}``.
    """
    if extra_context is None:
    	extra_context = {}
    dictionary = {'params': kwargs}
    for key, value in extra_context.items():
        if callable(value):
            dictionary[key] = value()
        else:
            dictionary[key] = value
    c = RequestContext(request, dictionary)
    t = get_template(template)
    t.render(c)
    return HttpResponse(render_template_block(t, block, c), mimetype=mimetype)

def render_to(template):
    """
    Decorator for Django views that sends returned dict to render_to_response function
    with given template and RequestContext as context instance.

    If view doesn't return dict then decorator simply returns output.
    Additionally view can return two-tuple, which must contain dict as first
    element and string with template name as second. This string will
    override template name, given as parameter

    Parameters:

     - template: template name to use
    """
    def renderer(func):
        def wrapper(request, *args, **kw):
            output = func(request, *args, **kw)
            if isinstance(output, (list, tuple)):
                return render_to_response(output[1], output[0], RequestContext(request))
            elif isinstance(output, dict):
                return render_to_response(template, output, RequestContext(request))
            return output
        return wrapper
    return renderer