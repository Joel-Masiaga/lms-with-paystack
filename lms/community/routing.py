"""
WebSocket URL routing for the community app.
Defines the WebSocket endpoints and their corresponding consumers.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Direct message WebSocket endpoint
    re_path(
        r'ws/chat/direct/(?P<user_id>\d+)/$',
        consumers.DirectMessageConsumer.as_asgi(),
        name='websocket_direct_chat'
    ),
    
    # Group message WebSocket endpoint
    re_path(
        r'ws/chat/group/(?P<group_id>\d+)/$',
        consumers.GroupMessageConsumer.as_asgi(),
        name='websocket_group_chat'
    ),
    
    # Typing indicator WebSocket endpoints
    re_path(
        r'ws/typing/direct/(?P<user_id>\d+)/$',
        consumers.TypingIndicatorConsumer.as_asgi(),
        name='websocket_typing_direct'
    ),
    
    re_path(
        r'ws/typing/group/(?P<group_id>\d+)/$',
        consumers.TypingIndicatorConsumer.as_asgi(),
        name='websocket_typing_group'
    ),
]
