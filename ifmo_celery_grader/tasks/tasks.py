from ifmo_celery_grader.tasks.helpers import GraderTaskBase, submit_task_grade
import requests


class AcademyTask(GraderTaskBase):

    def grade(self, student_input, grader_payload):
        r = requests.get('https://htmlacademy.ru/api/get_progress?course=basic&ifmo_user_id=148838')
        return r.text

    def grade_success(self, response):
        pass


def grade_academy():
    submit_task_grade(AcademyTask(), student_input={}, grader_payload={'course': 'basic', 'user_id': '148838'})
    pass