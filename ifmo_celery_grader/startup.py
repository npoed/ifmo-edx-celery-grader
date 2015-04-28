from django.conf import settings
from django.conf.urls import include, url
from path import path

import edxmako
import json
import logging


log = logging.getLogger(__name__)


def patch_templates():
    template_path = path(__file__).dirname() / 'templates'
    edxmako.paths.add_lookup('main', template_path, prepend=True)


def _patch_variant_url(app_name, urls_module):
    app_urls = __import__('%s.urls' % (app_name,), fromlist=['urlpatterns'])
    app_urls.urlpatterns.insert(0, url(r'', include(urls_module)))


def patch_urls():
    for (app, urls) in [('lms', 'ifmo_celery_grader.urls')]:
        try:
            _patch_variant_url(app, urls)
        except Exception:
            pass


def run():
    patch_templates()
    patch_urls()


