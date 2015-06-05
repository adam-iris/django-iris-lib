from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

"""
Define an inclusion tag for displaying
the correct URL builder
"""

"""
Renderer
"""
class BuilderSelector(template.Node):
    """
    """

"""
Compilation function
"""
def builder_selector(parser, token):
    """
    Custom Django templatetag to
    determine which builder
    to display
    """
    try:
        pass
        # return value.lower()
    except ValueError:
       raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split
