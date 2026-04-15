# Django Channels - Asynchronous Community Chat Implementation

## Overview
This document describes the migration of the community app to asynchronous programming using Django Channels for real-time, live chat functionality.

## Architecture

### Components Implemented

#### 1. **ASGI Configuration** (`lms/asgi.py`)
- Replaced WSGI application with ASGI
- Configured `ProtocolTypeRouter` to route between HTTP and WebSocket protocols
- Integrated `AuthMiddlewareStack` for WebSocket authentication
- Imported community app routing

#### 2. **Django Settings Update** (`lms/settings.py`)
- Added `daphne` and `channels` to INSTALLED_APPS
- Set `ASGI_APPLICATION = 'lms.asgi.application'`
- Configured `CHANNEL_LAYERS`:
  - **Development**: InMemoryChannelLayer (no Redis required)
  - **Production**: RedisChannelLayer (requires Redis server)

#### 3. **WebSocket Consumers** (`community/consumers.py`)
Three main consumer classes:

- **DirectMessageConsumer**: Handles 1-on-1 direct message conversations
  - Real-time message broadcasting between two users
  - Message persistence in database
  - Mark-as-read functionality
  - Method: `chat_message` event handling

- **GroupMessageConsumer**: Handles group chat conversations
  - Real-time group messaging
  - User join/leave notifications
  - Message persistence in database
  - Methods: `chat_message`, `user_joined`, `user_left`

- **TypingIndicatorConsumer**: Shows real-time typing status
  - Notifies when users are typing or stop typing
  - Works for both direct and group conversations
  - Methods: `user_typing`, `user_stopped_typing`

#### 4. **WebSocket Routing** (`community/routing.py`)
WebSocket URL patterns:
```python
- ws/chat/direct/<user_id>/      # Direct message chat
- ws/chat/group/<group_id>/      # Group message chat
- ws/typing/direct/<user_id>/    # Direct message typing indicator
- ws/typing/group/<group_id>/    # Group message typing indicator
```

#### 5. **JavaScript Client** (`community/static/community/js/websocket-client.js`)
Client-side WebSocket management with classes:

- **ChatWebSocketClient**: Base WebSocket connection handler
  - Connect, disconnect, send messages
  - Automatic reconnection logic
  - Event handler registration/removal

- **TypingIndicatorManager**: Manages typing indicators
  - `startTyping()`: Notify others user is typing
  - `stopTyping()`: Notify typing complete
  - Displays real-time typing status

- **MessageManager**: DOM manipulation for messages
  - `addMessage()`: Insert messages into chat
  - `scrollToBottom()`: Auto-scroll to latest message
  - HTML escaping for security

- **FileUploadManager**: File attachment handling
  - Upload via FormData
  - File size validation
  - Success/error callbacks

#### 6. **HTMX Integration** (`community/async_utils.py`)
Endpoints for dynamic updates:
- `upload_message_attachment()`: Upload file attachments
- `upload_group_message_attachment()`: Upload group attachments
- `load_message_history()`: Paginated message history
- `load_group_message_history()`: Group message history

#### 7. **Template Updates**
- **unified_conversation_detail.html**: Main chat interface
  - Includes WebSocket client library
  - Initialization script with message handling
  - Form IDs for JavaScript interaction

- **websocket_chat_init.html**: Chat WebSocket initialization
  - Establishes WebSocket connections
  - Sets up event handlers
  - Integrates typing indicators

- **Message includes**: Template partials for rendering messages
  - `direct_message_item.html`: Direct message rendering
  - `group_message_item.html`: Group message rendering

## Key Features

### ✅ Real-Time Messaging
- Messages appear instantly in all connected clients
- No page refresh required
- Database persistence with metadata

### ✅ Typing Indicators
- See when others are typing
- Real-time status updates
- Works for both 1-on-1 and group chats

### ✅ Authentication
- WebSocket connections validated through Django auth
- Prevents unauthorized access
- Uses existing user authentication

### ✅ File Attachments
- Support for images, videos, audio, documents
- 50 MB file size limit
- MIME type detection for proper rendering

### ✅ User Join/Leave Notifications
- Notified when members join/leave groups
- Includes member name and timestamp

### ✅ Automatic Reconnection
- Detects connection loss
- Attempts automatic reconnection (up to 10 times)
- Graceful degradation with error messages

### ✅ Message History
- Load historical messages via HTMX
- Pagination support
- Memory efficient for large conversations

### ✅ Backward Compatibility
- All existing features preserved
- HTTP endpoints still functional
- Supports both WebSocket and fallback modes

## Running the Application

### Development Environment

#### 1. Install Dependencies
```bash
cd paystacklms
pip install channels daphne channels-redis
```

#### 2. Run Daphne Development Server
```bash
cd lms
daphne -b 127.0.0.1 -p 8000 lms.asgi:application
```

Or with auto-reload and verbose logging:
```bash
daphne -b 127.0.0.1 -p 8000 -v 3 lms.asgi:application
```

#### 3. Access Application
- Open browser: `http://localhost:8000`
- Navigate to community hub
- Open two browser windows for testing chats

### Production Environment

#### 1. Install Redis
```bash
# Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:latest

# Or use Redis for Windows from https://github.com/microsoftarchive/redis/releases
```

#### 2. Update Settings
```python
# In lms/settings.py
ENVIRONMENT = 'production'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis-server-ip', 6379)],  # Your Redis server
            'capacity': 1500,
            'expiry': 10,
        },
    }
}
```

#### 3. Run Daphne with Supervision
```bash
# Using systemd
sudo systemctl start daphne@lms

# Using Supervisor
supervisord -c /path/to/supervisord.conf

# Using Docker
docker run -d -p 8000:8000 \
  -v /path/to/project:/app \
  --name lms-channels \
  daphne -b 0.0.0.0 -p 8000 lms.asgi:application
```

## Testing

### 1. Verify WebSocket Connection
```javascript
// In browser console
ws = new WebSocket('ws://localhost:8000/ws/chat/direct/2/');
ws.onopen = () => console.log('Connected');
ws.send(JSON.stringify({type: 'chat_message', message: 'Hello'}));
```

### 2. Test with Multiple Tab
- Open chat in tab 1
- Open chat with same user in tab 2
- Send message in tab 1
- Verify it appears in tab 2 instantly

### 3. Test Typing Indicators
- Start typing in message input
- Observe typing indicator in other browser

### 4. Test File Upload
- Click attachment button
- Select file
- Message should include file download link

### 5. Test Group Chats
- Create/join a group
- Send messages to group
- Verify all members see messages in real-time

## Database Models Used

```python
DirectMessage
- id, sender, recipient, content, attachment, created_at, is_read

GroupMessage  
- id, group, sender, content, attachment, created_at, updated_at

CommunityGroup
- id, name, description, icon, creator, members, created_at, updated_at, is_public

GroupMember
- id, user, group, role, joined_at
```

## Performance Considerations

### Channel Layers
- **Development**: InMemoryChannelLayer (single process only)
- **Production**: RedisChannelLayer (supports multiple processes/servers)

### Message History
- Paginate to limit database queries
- Cache popular messages if needed
- Archive old conversations for large groups

### Connection Limits
- Monitor active WebSocket connections
- Set reasonable connection timeouts
- Implement rate limiting for message frequency

## Security

### Authentication
- ✅ WebSocket uses Django auth middleware
- ✅ Only authenticated users can connect
- ✅ Users can only access their own conversations

### Authorization
- ✅ Group membership required for group chats
- ✅ Public groups allow view-only access
- ✅ Admin-only group edit operations

### Input Validation  
- ✅ HTML escaping for message content
- ✅ File type validation
- ✅ File size limits enforced
- ✅ CSRF protection on HTTP endpoints

## Troubleshooting

### WebSocket Not Connecting
1. Check Daphne is running: `daphne -b 127.0.0.1 -p 8000 lms.asgi:application`
2. Verify browser console for connection errors
3. Check firewall allows WebSocket ports
4. Ensure user is authenticated

###Messages Not Persisting
1. Run migrations: `python manage.py migrate`
2. Check database connection in settings
3. Verify DirectMessage and GroupMessage tables exist

### Typing Indicators Not Showing
1. Check browser console for WebSocket errors
2. Verify typing consumer is routing correctly
3. Check browser has adequate memory

### High CPU Usage
1. Check number of active WebSocket connections
2. Monitor Redis memory usage (if using production setup)
3. Implement connection timeouts
4. Check for message flood attacks

## Future Enhancements

- [ ] Message search functionality
- [ ] Message reactions/emojis
- [ ] Voice/video calling integration
- [ ] Message encryption end-to-end
- [ ] Message read receipts
- [ ] Unread message badges
- [ ] Message threading/replies
- [ ] Rich text editor support
- [ ] Media preview thumbnails
- [ ] Admin message moderation tools

## Files Modified/Created

### Modified Files
- `lms/settings.py` - Added Channels configuration
- `lms/asgi.py` - Updated with ProtocolTypeRouter
- `community/urls.py` - Added async utility routes
- `community/templates/community/unified_conversation_detail.html` - Added WebSocket script

### New Files Created
- `community/consumers.py` - WebSocket consumers
- `community/routing.py` - WebSocket URL patterns
- `community/async_utils.py` - HTMX endpoints
- `community/static/community/js/websocket-client.js` - JavaScript client
- `community/templates/community/includes/websocket_chat_init.html` - Initialization script
- `community/templates/community/includes/direct_message_item.html` - Message template
- `community/templates/community/includes/group_message_item.html` - Group message template

## References

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Daphne ASGI Server](https://github.com/django/daphne)
- [Django ASGI](https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
