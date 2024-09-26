# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from shop.routing import application  # Adjust import based on your app structure

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enoch_shopping.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/chat/general/", ChatConsumer.as_asgi()),  # Same as in routing.py
        ])
    ),
})
