import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import Room, Message, UserStatus
from channels.db import database_sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Determine the group name based on URL (room vs private)
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        room_id = self.scope['url_route']['kwargs'].get('room_id')
        username = self.scope['url_route']['kwargs'].get('username')
        if room_id:
            # Group chat room
            self.room_group_name = f"room_{room_id}"
        elif username:
            # 1-to-1 inbox (group per user)
            self.room_group_name = f"inbox_{username}"
        else:
            await self.close()
            return

        # Join the channel layer group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Mark user as online
        if hasattr(self.user, "userstatus"):
            await self.mark_online()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Mark user as offline
        if hasattr(self.user, "userstatus"):
            await self.mark_offline()

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        # Handle a chat message
        if msg_type == 'chat.message':
            content = data['message']
            sender = self.user
            # Persist message to database
            room = None
            if 'room_id' in self.scope['url_route']['kwargs']:
                room = await database_sync_to_async(Room.objects.get)(id=self.scope['url_route']['kwargs']['room_id'])
            # For private: you could create/get a Room or skip DB
            # Save the message
            message = Message.objects.create(room=room, sender=sender, content=content)
            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', 
                    'message': content,
                    'sender': sender.username,
                    'timestamp': str(message.timestamp)
                }
            )
        # Handle typing indicator
        elif msg_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'typing', 'username': self.user.username, 'is_typing': data.get('is_typing', False)}
            )
        # Handle read receipt
        elif msg_type == 'read':
            message_id = data.get('message_id')
            # Update message read flag (and broadcast back to sender)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'read', 'message_id': message_id, 'reader': self.user.username}
            )

    # Event handler for chat messages
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    # Event handler for typing notifications
    async def typing(self, event):
        # Don't notify the user who is typing about themselves
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    # Event handler for read receipts
    async def read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_id': event['message_id'],
            'reader': event['reader'],
        }))

    async def mark_online(self):
        # Update user's status in database (synchronous for demo)
        UserStatus.objects.update_or_create(user=self.user, defaults={'is_online': True})

    async def mark_offline(self):
        UserStatus.objects.filter(user=self.user).update(is_online=False)
