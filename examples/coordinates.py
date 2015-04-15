from django import forms
from django.views.generic.edit import FormView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import FormActions
from lib.coordinates import Coordinates
from lib.form_mixins import FormHelperMixin


class CoordinatesForm(FormHelperMixin, forms.Form):
    
    max_lat = forms.DecimalField()
    min_lat = forms.DecimalField()
    max_lon = forms.DecimalField()
    min_lon = forms.DecimalField()
    
    def create_form_layout(self):
        return Layout(
            Coordinates('max_lat', 'min_lat', 'max_lon', 'min_lon',
                css_id='location', label_html=_('Coordinates')),
            FormActions(
                Submit('save', 'Save changes'),
            )
        )


class CoordinatesView(FormView):
    template_name = 'examples/coordinates.html'
    form_class = CoordinatesForm
        
    