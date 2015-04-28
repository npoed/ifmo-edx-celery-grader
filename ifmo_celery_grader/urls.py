from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.generic.base import RedirectView

urlpatterns = patterns('',
    url(r'^dnth$', 'ifmo_celery_grader.views.do_nothing'),
)
