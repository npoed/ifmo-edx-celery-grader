from django.contrib.auth.models import User
from ifmo_celery_grader.tasks.helpers import GraderTaskBase, submit_task_grade
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey, UsageKey
from courseware.models import StudentModule
from ifmo_celery_grader.models import GraderTask
from celery.states import SUCCESS, FAILURE, STARTED

import json
import requests

ANT_URL = ''
ANT_ATTEMPTS_URL = 'http://de.ifmo.ru/api/public/courseAttempts?pid=%(user)s&courseid=%(course)s&unitid=%(unit)s'


class DelayedAntGraderTask(GraderTaskBase):
    """
    This one checks whether lab has been ever started.
    """

    def grade(self, student_input, grader_payload):
        return {}

    def grade_success(self, student_input, grader_payload, system_payload, system, response):

        module = system.get('module')
        state = json.loads(module.state)

        result = requests.get(ANT_ATTEMPTS_URL % {
            'user': student_input.get('user_id'),
            'course': grader_payload.get('ant_course_id'),
            'unit': grader_payload.get('ant_unit_id')
        })
        attempts_data = json.loads(result.text)
        latest_attempt = attempts_data['attempts'][-1]

        if latest_attempt.get('end') is None:
            state['ant_status'] = 'RUNNING'
            new_task = reserve_task(None, save=True,
                                    grader_payload=grader_payload,
                                    system_payload=system_payload,
                                    student_input=student_input,
                                    task_type='ANT_CHECK_DELAYED')
            submit_ant_check(new_task)

        else:
            state['ant_status'] = 'IDLE'

        module.state = json.dumps(state)
        module.save()


class AntCheckTask(GraderTaskBase):

    def grade(self, student_input, grader_payload):

        result = requests.get(ANT_ATTEMPTS_URL % {
            'user': student_input.get('user_id'),
            'course': grader_payload.get('ant_course_id'),
            'unit': grader_payload.get('ant_unit_id')
        })
        return json.loads(result.text)

    def grade_success(self, student_input, grader_payload, system_payload, system, response):

        task = system.get('task')
        module = system.get('module')
        state = json.loads(module.state)

        # if state.get('celery_task_id') == task.task_id:

        latest_attempt = response['attempts'][-1]
        module.max_grade = float(100)
        module.grade = latest_attempt.get('result', 0)
        state['ant_result'] = json.dumps(response)
        state['attempts'] = len(response['attempts'])
        state['ant_status'] = 'RUNNING' if latest_attempt.get('end') is None else 'IDLE'
        module.state = json.dumps(state)
        if module.grade is not None:
            module.score = module.grade / module.max_grade * grader_payload.get('max_score', 1)
        else:
            module.score = None
        module.save()


def submit_delayed_ant_precheck(task):
    """
    First of all we want to check whether ANT LMS has started.
    :return:
    """
    return submit_task_grade(DelayedAntGraderTask, task, countdown=20)


def submit_ant_check(task, countdown=None):
    if countdown is None:
        countdown = task.grader_payload.get('ant_time_limit')*60
    return submit_task_grade(AntCheckTask, task, countdown=countdown)


def reserve_task(xblock=None, save=False, grader_payload=None, system_payload=None, student_input=None, task_type=None):
    task = GraderTask.create(grader_payload=grader_payload, student_input=student_input, task_type=task_type,
                             system_payload=system_payload)
    system_payload['task_id'] = task.task_id
    task.system_payload = system_payload
    # Double-write is done here, how this can be escaped?
    task.save_now()
    if xblock is not None:
        xblock.celery_task_id = task.task_id
        if save:
            xblock.save_now()
    return task


def _update_module_state(module, state):
    module.state = json.dumps(state)
    module.save()