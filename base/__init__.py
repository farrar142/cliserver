from __future__ import absolute_import

import os
from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import InMemoryChannelLayer, get_channel_layer

from celery import Celery
from django.apps import apps

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
#REDIS_HOST = f"redis://:sbs123414@{ipchooser()}:6379/0"
app = Celery('base')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
#app.conf.task_default_queue = 'default'
# Load task modules from all registered Django apps.#
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
# print(app._get_backend())


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.task
def add(x, y):
    return x+y


@app.task
def model_save(model):
    print("test")
    model.save()
