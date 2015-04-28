from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models, transaction
from celery.states import PENDING
from uuid import uuid4


class GraderTask(models.Model):

    task_id = models.CharField(max_length=255, db_index=True)

    student_input = models.TextField(null=True)
    grader_payload = models.TextField(null=True)
    system_payload = models.TextField(null=True)

    task_input = models.TextField(null=True)
    task_output = models.TextField(null=True)

    # TODO: Add course_id, module_id, user_id
    course_id = models.CharField(max_length=255, null=True, db_index=True)
    module_id = models.CharField(max_length=255, null=True, db_index=True)
    user_target = models.ForeignKey(User, db_index=True, null=True)

    task_type = models.CharField(max_length=50, null=True, db_index=True)
    task_state = models.CharField(max_length=50, null=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, student_input=None, grader_payload=None, system_payload=None, task_type=None):

        task_id = str(uuid4())

        task = cls(
            task_id=task_id,
            student_input=student_input,
            grader_payload=grader_payload,
            system_payload=system_payload,
            task_state=PENDING,
            task_type=task_type
        )

        if system_payload is None:
            system_payload = dict()
        task.course_id = system_payload.get('course_id')
        task.module_id = system_payload.get('module_id')
        user_target = system_payload.get('user_id')
        if user_target is not None:
            task.user_target = User.objects.get(id=user_target)
        task.save_now()

        return task

    @transaction.autocommit
    def save_now(self):
        self.save()
