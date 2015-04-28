# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'GraderTask.system_payload'
        db.add_column('ifmo_celery_grader_gradertask', 'system_payload',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'GraderTask.system_payload'
        db.delete_column('ifmo_celery_grader_gradertask', 'system_payload')


    models = {
        'ifmo_celery_grader.gradertask': {
            'Meta': {'object_name': 'GraderTask'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'grader_payload': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'student_input': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'system_payload': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'task_input': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_output': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_state': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['ifmo_celery_grader']