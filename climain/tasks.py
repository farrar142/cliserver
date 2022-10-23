from __future__ import absolute_import
import json
from asgiref.sync import async_to_sync
from typing import Optional
from celery import Celery, shared_task
from base import app
from channels.layers import get_channel_layer, InMemoryChannelLayer


@shared_task
def send_ws_message(user_id, data):
    channel_layer: Optional[InMemoryChannelLayer] = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(f'ssh_{user_id}', data)
    return data
