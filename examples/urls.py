from django.conf.urls import patterns, include, url
from examples.coordinates import CoordinatesView
from examples.webservices import WebserviceView

urlpatterns = patterns('',
    url(r'coordinates/', CoordinatesView.as_view()),
    url(r'ws/', WebserviceView.as_view()),
)
