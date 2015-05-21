from celery import Task
from celery.states import SUCCESS, FAILURE, STARTED
from courseware.models import StudentModule
from ifmo_celery_grader.models import GraderTask
from opaque_keys.edx.keys import CourseKey, UsageKey

import json


class GraderTaskBase(Task):

    abstract = True

    def run(self, *args, **kwargs):

        # Get params data
        grader_payload = kwargs.get('grader_payload')
        system_payload = kwargs.get('system_payload')
        student_input = kwargs.get('student_input')

        # Change task status
        task = GraderTask.objects.get(task_id=system_payload.get('task_id'))
        # All params should be set on creating when pending
        task.task_state = STARTED
        task.save()

        try:
            return self.grade(student_input, grader_payload)
        except NotImplementedError:
            pass

        return

    def on_success(self, retval, task_id, args, kwargs):

        # Get params data
        grader_payload = kwargs.get('grader_payload')
        system_payload = kwargs.get('system_payload')
        student_input = kwargs.get('student_input')

        # Change task status
        task = GraderTask.objects.get(task_id=system_payload.get('task_id'))
        task.task_state = SUCCESS
        task.task_output = retval
        task.save_now()

        # Update payload and inject module there
        course_key = CourseKey.from_string(system_payload.get('course_id'))
        usage_key = UsageKey.from_string(system_payload.get('module_id'))
        module = StudentModule.objects.get(student_id=system_payload.get('user_id'),
                                           course_id=course_key,
                                           module_state_key=usage_key)

        system = {
            'task': task,
            'module': module,
        }

        # Should we handle errors here?
        try:
            self.grade_success(student_input, grader_payload, system_payload, system, retval)
        except NotImplementedError:
            pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):

        task = GraderTask.objects.get(task_id=task_id)
        task.task_state = FAILURE
        task.task_output = exc.message
        task.save()

    def after_return(self, status, retval, task_id, args, kwargs, einfo):

        system_payload = kwargs.get('system_payload')

        # Update payload and inject module there
        course_key = CourseKey.from_string(system_payload.get('course_id'))
        usage_key = UsageKey.from_string(system_payload.get('module_id'))
        module = StudentModule.objects.get(student_id=system_payload.get('user_id'),
                                           course_id=course_key,
                                           module_state_key=usage_key)

        state = json.loads(module.state)
        state['celery_task_id'] = None
        module.state = json.dumps(state)
        module.save()

    def grade(self, student_input, grader_payload):
        raise NotImplementedError()

    def grade_success(self, student_input, grader_payload, system_payload, system, response):
        raise NotImplementedError()


def submit_task_grade(task_class, task, countdown=0):

    task_data = {
        'student_input': task.student_input,
        'grader_payload': task.grader_payload,
        'system_payload': task.system_payload,
    }
    task_class().apply_async(task_id=task.task_id, kwargs=task_data, countdown=countdown, add_to_parent=False)

    return task


def reserve_task(xblock=None, save=False, grader_payload=None, system_payload=None, student_input=None, task_type=None):
    task = GraderTask.create(grader_payload=grader_payload, student_input=student_input, task_type=task_type,
                             system_payload=system_payload)
    system_payload['task_id'] = task.task_id
    task.system_payload = system_payload
    # Double-write is done here, how this can be escaped?
    task.save_now()
    if xblock is not None:
        if hasattr(xblock, 'celery_task_id'):
            xblock.celery_task_id = task.task_id
        # Explicit save is needed for StudentModule to be guarantee created
        # Though must it be task-manager concern?
        if save and hasattr(xblock, 'save_now'):
            xblock.save_now()
    return task