# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GraderTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=255, db_index=True)),
                ('student_input', models.TextField(null=True)),
                ('grader_payload', models.TextField(null=True)),
                ('system_payload', models.TextField(null=True)),
                ('task_input', models.TextField(null=True)),
                ('task_output', models.TextField(null=True)),
                ('course_id', models.CharField(max_length=255, null=True, db_index=True)),
                ('module_id', models.CharField(max_length=255, null=True, db_index=True)),
                ('task_type', models.CharField(max_length=50, null=True, db_index=True)),
                ('task_state', models.CharField(max_length=50, null=True, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user_target', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
