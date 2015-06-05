from crispy_forms.layout import LayoutObject, TEMPLATE_PACK
from django.utils.log import getLogger
from django.template.loader import render_to_string
from django.conf import settings

LOGGER = getLogger(__name__)


class CoordinatesFormMixin(object):
    class Media:
        css = {
            'all': (
                '//cdn.jsdelivr.net/qtip2/2.2.1/jquery.qtip.css',
                'coordinate_picker/coordinate_picker.css',
            )
        }
        js = (
            '//maps.googleapis.com/maps/api/js',
            '//cdn.jsdelivr.net/qtip2/2.2.1/jquery.qtip.js',
            'coordinate_picker/coordinate_picker.js',
        )


class Coordinates(LayoutObject):
    """
    Layout object to render N/S/E/W inputs and a button to trigger a popup map selector
    """
    template = "coordinate_picker/layout.html"
    
    def __init__(self, *fields, **kwargs):
        if len(fields) != 4:
            raise Exception("Coordinates requires 4 fields")
        self.fields = list(fields)
        self.css_class = kwargs.pop('css_class', None)
        self.css_id = kwargs.pop('css_id', None)
        self.template = kwargs.pop('template', self.template)
        self.label_html = kwargs.pop('label_html', None)
        self.help_text = kwargs.pop('help_text', None)
    
    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.template
        LOGGER.info("Coordinates")
        subfields = {}
        for i in range(4):
            label = 'nsew'[i]
            field = self.fields[i]
            subfields[label] = form[field]
            LOGGER.info("Subfield: %s" % subfields[label].field)
        return render_to_string(
            template,
            {'wrapper': self, 'subfields': subfields},
            context
        )    
