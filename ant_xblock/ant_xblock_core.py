# -*- coding: utf-8 -*-

from ifmo_celery_grader.models import GraderTask
from ant_xblock.ant_xblock_fields import AntXBlockFields
from ant_xblock import utils as ant_utils
from celery.states import PENDING
from courseware.models import StudentModule
from django.contrib.auth.models import User
from xblock.core import XBlock
from xblock.fragment import Fragment
from webob.exc import HTTPFound
from django.db import transaction

import json
import requests

from ant_xblock.tasks import submit_delayed_ant_precheck, submit_ant_check, reserve_task


class AntXBlock(AntXBlockFields, XBlock):

    icon_class = 'problem'
    has_score = True
    # always_recalculate_grades = True

    def student_view(self, context):

        # is there any other way to get user role?

        template_context = self._get_student_context()

        fragment = Fragment()
        fragment.add_content(self._render_template('static/templates/student_view.html', template_context))
        fragment.add_javascript(self._get_resource('static/js/student_view.js'))
        fragment.initialize_js('AntXBlockShow')
        return fragment

    def studio_view(self, context):

        template_context = {
            'metadata': json.dumps({
                'display_name': self.display_name,
                'course_id': self.ant_course_id,
                'unit_id': self.ant_unit_id,
                'content': self.content,
                'time_limit': self.ant_time_limit,
                'attempts_limit': self.ant_attempts_limit,
            }),
        }

        fragment = Fragment()
        fragment.add_content(self._render_template('static/templates/studio_view.html', template_context))
        fragment.add_javascript(self._get_resource('static/js/studio_view.js'))
        fragment.initialize_js('AntXBlockEdit')
        return fragment

    def get_score(self):
        return {
            'score': 0,
        }

    def max_score(self):
        return self.points

    @XBlock.handler
    def start_lab(self, request, suffix=''):

        # from xmodule.modulestore.django import modulestore
        # print dir(modulestore())

        lab_meta = {
            'sso_id': User.objects.get(id=self.scope_ids.user_id),
            'course_id': self.ant_course_id,
            'unit_id': self.ant_unit_id,
        }

        # Plan checking task
        need_new_task = False
        if self.celery_task_id is None:
            need_new_task = True
        else:
            try:
                task = GraderTask.objects.get(task_id=self.celery_task_id)
                if task.task_state != PENDING:
                    need_new_task = True
            except GraderTask.DoesNotExist:
                need_new_task = True

        need_new_task = True
        if need_new_task:
            task = reserve_task(self,
                                grader_payload=self._get_grader_payload(),
                                system_payload=self._get_system_payload(),
                                student_input=self._get_student_input(),
                                save=True,
                                task_type='ANT_START')
            # Do we really need this?
            self.celery_task_id = submit_delayed_ant_precheck(task).task_id

        self.save_now()

        # Register user for course in ant lms first
        register_url = 'http://de.ifmo.ru/api/public/getCourseAccess?pid=%(sso_id)s&courseid=%(course_id)s' % lab_meta
        requests.post(register_url)

        # Do actual redirect
        lab_url = ('http://de.ifmo.ru/IfmoSSO?redirect='
                   'http://de.ifmo.ru/servlet/%%3FRule=EXTERNALLOGON%%26COMMANDNAME=getCourseUnit%%26'
                   'DATA=UNIT_ID=%(unit_id)s|COURSE_ID=%(course_id)s') % lab_meta

        return HTTPFound(location=lab_url)

    @XBlock.json_handler
    def check_lab(self, data, suffix=''):
        # Plan checking task
        task_data = self._get_task_data()
        task = reserve_task(self,
                            grader_payload=self._get_grader_payload(),
                            system_payload=self._get_system_payload(),
                            student_input=self._get_student_input(),
                            save=True,
                            task_type='ANT_CHECK')
        submit_ant_check(task, countdown=0)
        return 'test'

    @XBlock.json_handler
    def save_settings(self, data, suffix=''):
        self.display_name = data.get('display_name')
        self.ant_course_id = data.get('course_id', '')
        self.ant_unit_id = data.get('unit_id', '')
        self.content = data.get('content', '')
        self.ant_time_limit = data.get('time_limit', 0)
        self.ant_attempts_limit = data.get('attempts_limit', 0)
        return '{}'

    @XBlock.json_handler
    def get_user_data(self, data, suffix=''):
        user_id = data.get('user_id')
        module = StudentModule.objects.get(module_state_key=self.location,
                                           student__username=user_id)
        return {
            'state': module.state,
        }

    @transaction.autocommit
    def save_now(self):
        self.save()

    def _get_student_context(self, user=None):
        return {
            'student_state': json.dumps(
                {
                    'score': {
                        'earned': self.score,
                        'max': self.weight,
                    },
                    'attempts': {
                        'used': self.attempts,
                        'limit': self.ant_attempts_limit,
                    },
                    'time': {
                        'limit': self.ant_time_limit,
                    },
                    'ant': {
                        'course': self.ant_course_id,
                        'unit': self.ant_unit_id,
                    },
                    'meta': {
                        'name': self.display_name,
                        'text': self.content,
                    },
                    'ant_status': self.ant_status,
                }
            ),
            'is_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),

            # This is probably studio, find out some more ways to determine this
            'is_studio': self.scope_ids.user_id is None
        }

    @staticmethod
    def _get_resource(file_name):
        return ant_utils.resource_string(file_name, package_name='ant_xblock')

    @staticmethod
    def _render_template(template_name, context=None):
        return ant_utils.render_template(template_name, context=context, package_name='ant_xblock')

    def _get_task_data(self):
        return {
            'user_id': self.scope_ids.user_id,
            'course_id': unicode(self.course_id),
            'module_id': unicode(self.location),
            'ant_course_id': self.ant_course_id,
            'ant_unit_id': self.ant_unit_id,
            'ant_time_limit': self.ant_time_limit,
            'max_score': self.weight,
        }

    def _get_grader_payload(self):
        """
        Данные, завясящие исключительно от модуля, но не возволяющие идентифицировать сам модуль.
        :return:
        """
        return {
            'ant_course_id': self.ant_course_id,
            'ant_unit_id': self.ant_unit_id,
            'ant_time_limit': self.ant_time_limit,
        }

    def _get_system_payload(self):
        """
        Данные, позволяющие идентифицировать сам модуль.
        :return:
        """
        return {
            'user_id': self.scope_ids.user_id,
            'course_id': unicode(self.course_id),
            'module_id': unicode(self.location),
            'max_score': self.weight,
        }

    def _get_student_input(self):
        return {
            'user_id': User.objects.get(id=self.scope_ids.user_id).username
        }
