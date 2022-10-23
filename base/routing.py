from django.urls import re_path, path
from climain.consumers import SSHConsumer
websocket_urlpatterns = [
    # re_path(r'ws/(?P<room_name>\w+)/(?P<user_id>\w+)/$',
    #         consumers.RTCConsumer.as_asgi()),
    re_path(r'ssh/(?P<user_id>\w+)/ws/$',
            SSHConsumer.as_asgi()),
]