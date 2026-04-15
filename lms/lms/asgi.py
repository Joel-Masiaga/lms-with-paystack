"""
ASGI config for lms project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')

# Initialize Django
django.setup()

# Import after Django setup
from community.routing import websocket_urlpatterns

# ASGI application that routes between HTTP and WebSocket protocols
application = ProtocolTypeRouter({
    # HTTP and WebSocket will be handled by Daphne
    "http": get_asgi_application(),
    
    # WebSocket chat handler with authentication
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
