from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/room/(?P<room_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chat/private/(?P<username>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chat/typing/(?P<room_id>\d+)/$', consumers.TypingConsumer.as_asgi()),
]
