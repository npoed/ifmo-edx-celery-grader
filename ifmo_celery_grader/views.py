# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.http import HttpResponseForbidden, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from student.models import UserProfile
from student.views import try_change_enrollment
from urllib import urlencode

import hashlib
import logging
import re
from ifmo_celery_grader.tasks.tasks import grade_academy

logger = logging.getLogger('ifmo_celery_grader')


def do_nothing(request):
    grade_academy()
    return HttpResponse('do nothing')
