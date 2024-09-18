from django.urls import re_path
from . import consumers  # Ensure this imports correctly

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),  # Adjust this as needed
]
