from django.contrib import admin
from ifmo_celery_grader.models import GraderTask


class GraderTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'module_id', 'user_target', 'task_type', 'task_state')
    list_filter = ('course_id', 'task_type', 'task_state')
    search_fields = ('task_id', 'course_id', 'module_id', 'user_target__username')


admin.site.register(GraderTask, GraderTaskAdmin)