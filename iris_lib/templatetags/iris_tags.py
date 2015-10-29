from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import re
from django.utils.log import getLogger
import json
from django.utils.encoding import force_text
from django.conf import settings
from django.template.loader import render_to_string

LOGGER = getLogger(__name__)
register = template.Library()

def obfuscate_string(value):
    '''
    Simple string obfuscator

    Source: https://github.com/morninj/django-email-obfuscator
    '''
    return ''.join(['&#{0:s};'.format(str(ord(char))) for char in value])


@register.filter
def keyvalue(d, key):
    """
    Forms expose fields like a dict, but they don't support get() or __contains__ so
    we need to just call and catch KeyError
    """
    if not hasattr(d, '__getitem__'):
        return None
    try:
        return d[key]
    except KeyError:
        return None


@register.simple_tag(takes_context=True)
def log_form_errors(context):
    """
    A template tag that logs form errors when the form is rerendered to the user.  This can be useful
    because normally the form-level errors are not recorded anywhere.
    """
    form = context.get('form')
    if form:
        form_errors = getattr(form, 'errors', None)
        if form_errors and isinstance(form_errors, dict):
            errors = {}
            for fname, error in form_errors.iteritems():
                val = '?'
                try:
                    val = form[fname].value()
                except: pass
                errors[fname] = [error, val]
            LOGGER.debug("Form errors: %s" % json.dumps(errors))
    return ''


##
# 2014-09-09 rnewman: email obfuscator

@register.filter
@stringfilter
def obfuscate(value):
    return mark_safe(obfuscate_string(value))

@register.filter
@stringfilter
def obfuscate_mailto(value, text=False):
    mail = obfuscate_string(value)
    if text:
        link_text = text
    else:
        link_text = mail
    return mark_safe('<a href="{0:s}{1:s}">{2:s}</a>'.format(
        obfuscate_string('mailto:'), mail, link_text))


# Bootstrap3 class to correspond with various Django status levels
BS3_STATUS_CLASSES = {
    'debug': 'default',
    'error': 'danger',
}

@register.filter
@stringfilter
def status_class(status):
    """
    Translates a Django status level (debug/info/success/warning/error) to a BS3 class
    """
    return BS3_STATUS_CLASSES.get(status, status)


@register.filter()
def link_dois(value):
    """
    Finds any DOI references in a block of text and renders them linked to dx.doi.org.
    """
    return mark_safe(re.sub(r'(?<!dx.doi.org/)(doi:\d+\.\d+/\S+\w)', r'<a href="http://dx.doi.org/\1">\1</a>', value))


#####
# Popup help tag
#
# Renders a help icon that pops up the given content on mouseover.
#
# @example:
# {% popuphelp %}
# <b>Here</b> is some help text! It can include HTML markup.
# {% endpopuphelp %}
#
# @example:
# {% popuphelp textile %}
# *Here* is some help text! It can include Textile markup.
# {% endpopuphelp %}

class PopupHelpNode(template.Node):
    def __init__(self, nodelist, options):
        self.nodelist = nodelist
        self.options = options
    def render(self, context):
        output = self.nodelist.render(context)
        if 'textile' in self.options:
            try:
                import textile
                output = mark_safe(textile.textile(force_text(output.strip())))
            except ImportError:
                if settings.DEBUG:
                    raise template.TemplateSyntaxError("Error in {% textile %} filter: The Python textile library isn't installed.")
        return render_to_string('iris_lib/popup_help.html', {'content': output})


@register.tag(name='popuphelp')
def do_popuphelp(parser, token):
    nodelist = parser.parse(('endpopuphelp',))
    parser.delete_first_token()
    options = token.split_contents()
    return PopupHelpNode(nodelist, options)


@register.filter()
@stringfilter
def first_paragraph(value):
    """ Take just the first paragraph of the HTML passed in.
    """
    paragraphs = value.split("</p>", 1)
    if len(paragraphs) > 1:
        return mark_safe(value.split("</p>")[0] + "</p>")
    else:
        return mark_safe(value)


#####
# Plaintext trimmer
#
# Removes excess newlines from a block of text. This is useful for templates that produce
# plaintext (eg. plaintext email), generally if there is any template logic it will result in lots
# of extra newlines, because the template will render the newlines between each line of control logic.
#
# This will:
# - Convert any run of 2+ newlines (with any whitespace between them) into "\n\n"
# - Strip any whitespace from the beginning and end of the resulting string
#
# @example:
# {% trimtext %}
#     {% if some_condition %}
#         {% for item in items %}
# {{ item }}
#        {% endfor %}
#     {% endif %}
# {% endtrimtext %}
#
# Note in the example that there will still be 2 newlines between each {{ item }}

class TrimTextNode(template.Node):
    def __init__(self, nodelist, options):
        self.nodelist = nodelist
    def render(self, context):
        output = self.nodelist.render(context)

        return re.sub(r'([^\S\n]*\n){2,}', r'\n\n', output).strip()

@register.tag(name='trimtext')
def do_trimtext(parser, token):
    nodelist = parser.parse(('endtrimtext',))
    parser.delete_first_token()
    options = token.split_contents()
    return TrimTextNode(nodelist, options)

