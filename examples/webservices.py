from django import forms
from django.views.generic.edit import FormView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import FormActions
from lib.coordinates import Coordinates
from lib.crispy_forms_mixins import FormHelperMixin


class WebserviceForm(FormHelperMixin, forms.Form):

    starttime = forms.RegexField(r'(\d+-){2}\d+T(\d+:){0,2}(\d+)?')
    endtime = forms.RegexField(r'(\d+-){2}\d+T(\d+:){0,2}(\d+)?')
    maxlat = forms.DecimalField()
    minlat = forms.DecimalField()
    maxlon = forms.DecimalField()
    minlon = forms.DecimalField()

    def create_form_layout(self):
        return Layout(
            'starttime',
            'endtime',
            Coordinates('maxlat', 'minlat', 'maxlon', 'minlon',
                css_id='location', label_html=_('Coordinates')),
            FormActions(
                Submit('save', 'Save changes'),
            )
        )


class WebserviceView(FormView):
    template_name = 'examples/webservices.html'
    form_class = WebserviceForm

    def post(self, request):
        return super(WebserviceView, self).post(request)
