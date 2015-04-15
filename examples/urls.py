from django.conf.urls import patterns, include, url
from examples.coordinates import CoordinatesView

urlpatterns = patterns('',
    url(r'coordinates/', CoordinatesView.as_view()),
)
