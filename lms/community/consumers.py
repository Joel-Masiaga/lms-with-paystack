"""
WebSocket consumers for real-time messaging in the community app.
Handles both direct messages and group messages using Django Channels.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import datetime

from .models import DirectMessage, GroupMessage, CommunityGroup, GroupMember, Conversation
from users.models import User


class DirectMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for direct message conversations.
    Handles real-time messaging between two users.
    """
    
    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.user = self.scope["user"]
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a unique room name for this conversation
        user_ids = sorted([self.user.id, int(self.other_user_id)])
        self.room_name = f"dm_{user_ids[0]}_{user_ids[1]}"
        self.room_group_name = f"chat_{self.room_name}"
        
        # Verify the other user exists
        other_user_exists = await self.verify_other_user()
        if not other_user_exists:
            await self.close()
            return
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark messages as read
        await self.mark_messages_as_read()
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the room group only if it was created
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Called when the server receives a message from the WebSocket.
        """
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            content = data.get('message', '').strip()
            attachment_path = data.get('attachment_path', None)
            attachment_url = data.get('attachment_url', None)
            
            # Allow message if it has content or attachment
            if not content and not attachment_path:
                return
            
            # Save message to database
            message = await self.save_message(content, attachment_path, attachment_url)
            
            # Debug log
            print(f"DM Message saved: ID={message['id']}, has_attachment={message.get('has_attachment')}, attachment_url={message.get('attachment_url')}")
            
            # Broadcast message to both users in the conversation
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message['content'],
                    'sender_id': message['sender_id'],
                    'sender_name': message['sender_name'],
                    'timestamp': message['timestamp'],
                    'iso_timestamp': message.get('iso_timestamp'),
                    'message_id': message['id'],
                    'has_attachment': message.get('has_attachment', False),
                    'attachment_url': message.get('attachment_url'),
                }
            )
    
    async def chat_message(self, event):
        """
        Broadcast message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'iso_timestamp': event.get('iso_timestamp'),
            'message_id': event['message_id'],
            'has_attachment': event.get('has_attachment', False),
            'attachment_url': event.get('attachment_url'),
        }))
    
    @database_sync_to_async
    def verify_other_user(self):
        """Verify that the other user exists."""
        try:
            User.objects.get(id=self.other_user_id)
            return True
        except User.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, attachment_path=None, attachment_url=None):
        """Save a direct message to the database."""
        from django.core.files.storage import default_storage
        
        other_user = User.objects.get(id=self.other_user_id)
        
        # Create message with attachment if provided
        message_data = {
            'sender': self.user,
            'recipient': other_user,
            'content': content
        }
        
        # If attachment path is provided, set it
        if attachment_path:
            # Verify file exists in storage
            if default_storage.exists(attachment_path):
                message_data['attachment'] = attachment_path
                print(f"Attaching file: {attachment_path}")
            else:
                print(f"WARNING: File not found in storage: {attachment_path}")
        
        message = DirectMessage.objects.create(**message_data)
        
        # Get or create conversation
        conversation = Conversation.objects.filter(
            participants=self.user
        ).filter(participants=other_user).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(self.user, other_user)
        
        # Refresh message to get the actual attachment URL from storage
        message.refresh_from_db()
        
        # Get timezone-aware timestamp
        from django.utils import timezone
        local_time = timezone.localtime(message.created_at)
        iso_timestamp = local_time.isoformat()
        
        return {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'timestamp': local_time.strftime('%H:%M'),
            'iso_timestamp': iso_timestamp,
            'has_attachment': bool(message.attachment),
            'attachment_url': message.attachment.url if message.attachment else None,
        }
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all unread messages from the other user as read."""
        DirectMessage.objects.filter(
            sender_id=self.other_user_id,
            recipient=self.user,
            is_read=False
        ).update(is_read=True)


class GroupMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for group message conversations.
    Handles real-time messaging in community groups.
    """
    
    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.user = self.scope["user"]
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f"group_{self.group_id}"
        self.successfully_joined = False  # Track if we successfully joined
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user is a member of the group
        is_member = await self.verify_group_membership()
        if not is_member:
            await self.close()
            return
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        self.successfully_joined = True  # Mark as successfully joined
        
        # TODO: Re-enable user_joined notification after debugging notification system
        # Temporarily disabled due to notification display issues
        # Notify others that user has joined (only if user name is properly set)
        # user_name = self.user.get_full_name() or self.user.username
        # if user_name and user_name.strip():  # Ensure name is not empty
        #     await self.channel_layer.group_send(
        #         self.room_group_name,
        #         {
        #             'type': 'user_joined',
        #             'user_name': user_name,
        #             'user_id': self.user.id,
        #         }
        #     )
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Only notify and discard if we successfully joined
        if getattr(self, 'successfully_joined', False):
            # TODO: Re-enable user_left notification after debugging notification system
            # Temporarily disabled due to notification display issues
            # Notify others that user has left (only if user name is properly set)
            # user_name = self.user.get_full_name() or self.user.username
            # if user_name and user_name.strip():  # Ensure name is not empty
            #     await self.channel_layer.group_send(
            #         self.room_group_name,
            #         {
            #             'type': 'user_left',
            #             'user_name': user_name,
            #             'user_id': self.user.id,
            #         }
            #     )
            
            # Leave the room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Called when the server receives a message from the WebSocket.
        """
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            content = data.get('message', '').strip()
            attachment_path = data.get('attachment_path', None)
            attachment_url = data.get('attachment_url', None)
            
            # Allow message if it has content or attachment
            if not content and not attachment_path:
                return
            
            # Save message to database
            message = await self.save_message(content, attachment_path, attachment_url)
            
            # Debug log
            print(f"Group Message saved: ID={message['id']}, has_attachment={message.get('has_attachment')}, attachment_url={message.get('attachment_url')}")
            
            # Broadcast message to all members in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message['content'],
                    'sender_id': message['sender_id'],
                    'sender_name': message['sender_name'],
                    'sender_avatar': message['sender_avatar'],
                    'timestamp': message['timestamp'],
                    'iso_timestamp': message.get('iso_timestamp'),
                    'message_id': message['id'],
                    'has_attachment': message.get('has_attachment', False),
                    'attachment_url': message.get('attachment_url'),
                }
            )
    
    async def chat_message(self, event):
        """
        Broadcast message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'sender_avatar': event['sender_avatar'],
            'timestamp': event['timestamp'],
            'iso_timestamp': event.get('iso_timestamp'),
            'message_id': event['message_id'],
            'has_attachment': event.get('has_attachment', False),
            'attachment_url': event.get('attachment_url'),
        }))
    
    async def user_joined(self, event):
        """
        Handle user joined notification
        """
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
        }))
    
    async def user_left(self, event):
        """
        Handle user left notification
        """
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
        }))
    
    @database_sync_to_async
    def verify_group_membership(self):
        """Verify that the user is a member of the group."""
        try:
            group = CommunityGroup.objects.get(id=self.group_id)
            # Check if user is a member or group is public
            is_member = group.members.filter(id=self.user.id).exists()
            return is_member or group.is_public
        except CommunityGroup.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, attachment_path=None, attachment_url=None):
        """Save a group message to the database."""
        from django.core.files.storage import default_storage
        
        group = CommunityGroup.objects.get(id=self.group_id)
        
        # Create message with attachment if provided
        message_data = {
            'group': group,
            'sender': self.user,
            'content': content
        }
        
        # If attachment path is provided, set it
        if attachment_path:
            # Verify file exists in storage
            if default_storage.exists(attachment_path):
                message_data['attachment'] = attachment_path
                print(f"Attaching file to group message: {attachment_path}")
            else:
                print(f"WARNING: File not found in storage: {attachment_path}")
        
        message = GroupMessage.objects.create(**message_data)
        
        # Refresh message to get the actual attachment URL from storage
        message.refresh_from_db()
        
        # Get sender's avatar URL
        sender_avatar = ''
        if hasattr(self.user, 'profile') and self.user.profile.image:
            sender_avatar = self.user.profile.image.url
        
        # Get timezone-aware timestamp
        from django.utils import timezone
        local_time = timezone.localtime(message.created_at)
        iso_timestamp = local_time.isoformat()
        
        return {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() or message.sender.username,
            'sender_avatar': sender_avatar,
            'timestamp': local_time.strftime('%H:%M'),
            'iso_timestamp': iso_timestamp,
            'has_attachment': bool(message.attachment),
            'attachment_url': message.attachment.url if message.attachment else None,
        }


class TypingIndicatorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time typing indicators.
    Shows when other users are typing messages.
    """
    
    async def connect(self):
        """
        Called when a WebSocket connection is established.
        """
        self.user = self.scope["user"]
        self.conversation_type = self.scope['url_route']['kwargs'].get('conversation_type')
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        if self.conversation_type == 'direct':
            self.other_user_id = self.scope['url_route']['kwargs'].get('user_id')
            user_ids = sorted([self.user.id, int(self.other_user_id)])
            self.room_group_name = f"typing_dm_{user_ids[0]}_{user_ids[1]}"
        elif self.conversation_type == 'group':
            self.group_id = self.scope['url_route']['kwargs'].get('group_id')
            self.room_group_name = f"typing_group_{self.group_id}"
        else:
            await self.close()
            return
        
        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Only discard from group if we successfully joined it
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Called when the server receives a message from the WebSocket.
        """
        data = json.loads(text_data)
        
        if data.get('state') == 'start':
            # User is typing
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name() or self.user.username,
                }
            )
        elif data.get('state') == 'stop':
            # User stopped typing
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_stopped_typing',
                    'user_id': self.user.id,
                }
            )
    
    async def user_typing(self, event):
        """
        Handle user typing notification
        """
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
            }))
    
    async def user_stopped_typing(self, event):
        """
        Handle user stopped typing notification
        """
        if event['user_id'] != self.user.id:  # Don't send to self
            await self.send(text_data=json.dumps({
                'type': 'user_stopped_typing',
                'user_id': event['user_id'],
            }))
