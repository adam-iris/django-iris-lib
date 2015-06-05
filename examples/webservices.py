from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from iris_lib.ws_client.events import EventRequest
import datetime

class WebserviceView(TemplateView):
    template_name = 'examples/webservices.html'

    def get_context_data(self, **kwargs):
        context = super(WebserviceView, self).get_context_data(**kwargs)
        context['events'] = self.get_ws_data()
        return context
    
    def get_ws_data(self):
        req = EventRequest(
            startdate=datetime.datetime(2015, 1, 1),
            enddate=datetime.datetime(2015, 1, 5),
        )
        return req.get()
    