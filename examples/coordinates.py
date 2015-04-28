from django.utils.translation import ugettext as _
from django import forms
from django.views.generic.edit import FormView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import FormActions
from iris_lib.coordinates import Coordinates, CoordinatesFormMixin
from iris_lib.crispy_forms_mixins import FormHelperMixin
from logging import getLogger

LOGGER = getLogger(__name__)

class CoordinatesForm(FormHelperMixin, CoordinatesFormMixin, forms.Form):

    max_lat = forms.DecimalField()
    min_lat = forms.DecimalField()
    max_lon = forms.DecimalField()
    min_lon = forms.DecimalField()

    def create_form_layout(self):
        return Layout(
            Coordinates(nsew=('max_lat', 'min_lat', 'max_lon', 'min_lon',),
                css_id='location', label_html=_('Coordinates')),
            FormActions(
                Submit('save', 'Save changes'),
            )
        )


class CoordinatesView(FormView):
    template_name = 'examples/coordinates.html'
    form_class = CoordinatesForm

    def get_context_data(self, **kwargs):
        context = super(CoordinatesView, self).get_context_data(**kwargs)
        LOGGER.info("Form media: %s" % context['form'].media)
        return context

