import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from shop import routing as shop_routing

# Set the default settings module for the 'enoch_shopping' project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enoch_shopping.settings')

# Create the ASGI application
application = ProtocolTypeRouter({
    # Handle HTTP requests with the default Django ASGI application
    "http": get_asgi_application(),
    
    # Handle WebSocket connections
    "websocket": AuthMiddlewareStack(
        URLRouter(
            shop_routing.websocket_urlpatterns
        )
    ),
})
