# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GraderTask'
        db.create_table('ifmo_celery_grader_gradertask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('task_input', self.gf('django.db.models.fields.TextField')(null=True)),
            ('task_output', self.gf('django.db.models.fields.TextField')(null=True)),
            ('task_state', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('ifmo_celery_grader', ['GraderTask'])


    def backwards(self, orm):
        # Deleting model 'GraderTask'
        db.delete_table('ifmo_celery_grader_gradertask')


    models = {
        'ifmo_celery_grader.gradertask': {
            'Meta': {'object_name': 'GraderTask'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'task_input': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_output': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_state': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['ifmo_celery_grader']