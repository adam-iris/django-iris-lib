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
            'libs/gmaps/infobubble.js',
            'coordinate_picker/coordinate_picker.js',
        )


class Coordinates(LayoutObject):
    """
    Layout object to render N/S/E/W inputs and a button to trigger a popup map selector
    """
    template = "coordinate_picker/layout.html"
    
    def __init__(self, nsew=None, cr=None, **kwargs):
        if not (nsew or cr):
            raise Exception("Need one or both of NSEW or Center/Radius inputs")
        if nsew and len(nsew) != 4:
            raise Exception("NSEW coordinates requires 4 fields")
        self.nsew = nsew
        self.cr = cr
        self.css_class = kwargs.pop('css_class', None)
        self.css_id = kwargs.pop('css_id', None)
        self.template = kwargs.pop('template', self.template)
        self.label_html = kwargs.pop('label_html', None)
        self.help_text = kwargs.pop('help_text', None)
    
    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        LOGGER.info("Coordinates")
        if self.nsew and self.cr:
            template = 'coordinate_picker/layout_nsew_cr.html'
        elif self.nsew:
            template = 'coordinate_picker/layout_nsew.html'
        elif self.cr:
            template = 'coordinate_picker/layout_cr.html'
        subfields = {}
        if self.nsew:
            for i in range(4):
                label = 'nsew'[i]
                field = self.nsew[i]
                subfields[label] = form[field]
                LOGGER.info("Subfield: %s" % subfields[label].field)
        if self.cr:
            for i in range(len(self.cr)):
                label = ['center_lat', 'center_lon', 'max_radius', 'min_radius'][i]
                field = self.cr[i]
                subfields[label] = form[field]
                LOGGER.info("Subfield: %s" % subfields[label].field)
        return render_to_string(
            template,
            {'wrapper': self, 'subfields': subfields},
            context
        )    
