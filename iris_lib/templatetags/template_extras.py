from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.encoding import force_text, force_bytes
from django.utils.safestring import mark_safe
from textwrap import dedent
import re
from django.utils.log import getLogger
import json

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

##
# 2013-06-25 adam: copied from django.contrib.markup, since that is deprecated as of Django 1.5

@register.filter(is_safe=True)
def textile(value, args=''):
    try:
        import textile
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in 'textile' filter: The Python textile library isn't installed.")
        return force_text(value)
    else:
        auto_link = ("auto_link" in args)
        value_bytes = force_bytes(value)
        if auto_link:
            # Textile does web links but not email links, so do them here
            value_bytes = re.sub(r'\b(?:mailto:)?([\w.-]+\@[a-z0-9.\-]+[.][a-z]{2,4})\b', r'"\1":mailto:\1', value_bytes)
        return mark_safe(force_text(textile.textile(value_bytes, encoding='utf-8', output='utf-8', auto_link=auto_link)))

class TextileNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
    def render(self, context):
        output = self.nodelist.render(context)
        try:
            import textile
        except ImportError:
            if settings.DEBUG:
                raise template.TemplateSyntaxError("Error in {% textile %} filter: The Python textile library isn't installed.")
            return force_text(output)
        return textile.textile(force_text(dedent(output.strip())))

@register.tag(name='textile')
def do_textile(parser, token):
    nodelist = parser.parse(('endtextile',))
    parser.delete_first_token()
    return TextileNode(nodelist)

##
# 2013-09-05 rnewman: filter for checking existence of URL builder template

@register.filter(name="urlbuilder_exists")
def urlbuilder_exists(template_name):
    path_to_builder = "%s/%s.html" % ("webservicedoc/builders", template_name)
    try:
        template.loader.get_template(path_to_builder)
        return path_to_builder
    except template.TemplateDoesNotExist:
        return False


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
