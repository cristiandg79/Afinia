import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from accounts.date_labels import friendly_datetime
from accounts.models import Connection
from .chat_rooms import is_chat_conversation, is_chat_group
from .cleanup import trim_conversation_messages
from .models import MESSAGE_MAX_LENGTH, Conversation, Message
from .notifications import mark_conversation_read, notification_counts, notify_conversation_participants
from .presence import join_chat, leave_chat


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'conversation_{self.conversation_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.user_can_access_conversation():
            await self.close()
            return

        self.is_public_chat = await self.conversation_is_public_chat()
        self.is_presence_chat = await self.conversation_has_presence()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        if self.is_presence_chat:
            join_chat(self.conversation_id, self.user.id, self.channel_name)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.presence',
                    'participant': await self.current_participant_payload(),
                },
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            if getattr(self, 'is_presence_chat', False):
                should_notify_leave = leave_chat(self.conversation_id, self.user.id, self.channel_name)
                if should_notify_leave:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat.presence.leave',
                            'participant_id': self.user.id,
                        },
                    )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            return

        body = (payload.get('body') or '').strip()
        if not body:
            return
        if len(body) > MESSAGE_MAX_LENGTH:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'El mensaje no puede superar {MESSAGE_MAX_LENGTH} caracteres.',
            }))
            return

        message = await self.create_message(body)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': {
                    'id': message['id'],
                    'body': message['body'],
                    'sender_id': self.user.id,
                    'sender_name': message['sender_name'],
                    'sender_avatar_url': message['sender_avatar_url'],
                    'sender_initial': message['sender_initial'],
                    'created_at': message['created_at'],
                },
            },
        )
        await self.notify_unread_participants()

    async def chat_message(self, event):
        if event['message']['sender_id'] != self.user.id:
            read_message_ids = await self.mark_current_conversation_read()
            await self.send_notification_counts()
            if read_message_ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat.read',
                        'reader_id': self.user.id,
                        'message_ids': read_message_ids,
                    },
                )
        await self.send(text_data=json.dumps(event['message']))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'reader_id': event['reader_id'],
            'message_ids': event['message_ids'],
        }))

    async def chat_presence(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'participant': event['participant'],
        }))

    async def chat_presence_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence_leave',
            'participant_id': event['participant_id'],
        }))

    @sync_to_async
    def user_can_access_conversation(self):
        conversation = (
            Conversation.objects
            .filter(pk=self.conversation_id, participants=self.user)
            .prefetch_related('participants')
            .first()
        )
        if not conversation:
            return False
        if conversation.group_id or conversation.plan_id:
            return True
        other = conversation.participants.exclude(pk=self.user.pk).first()
        if not other:
            return True
        return not Connection.objects.filter(
            Q(requester=self.user, receiver=other) | Q(requester=other, receiver=self.user),
            status=Connection.Status.BLOCKED,
        ).exists()

    @sync_to_async
    def conversation_is_public_chat(self):
        conversation = Conversation.objects.select_related('group').get(pk=self.conversation_id)
        return is_chat_conversation(conversation)

    @sync_to_async
    def conversation_has_presence(self):
        conversation = Conversation.objects.select_related('group', 'plan').get(pk=self.conversation_id)
        return is_chat_conversation(conversation) or bool(
            (conversation.group and not is_chat_group(conversation.group)) or conversation.plan
        )

    @sync_to_async
    def current_participant_payload(self):
        try:
            profile = self.user.profile
        except ObjectDoesNotExist:
            profile = None
        details = []
        if profile and profile.age:
            details.append(f'{profile.age} años')
        if profile and profile.location_label:
            details.append(profile.location_label)
        return {
            'id': self.user.id,
            'username': self.user.username,
            'details': ' · '.join(details) or 'Sin datos de perfil',
            'avatar_url': profile.photo.url if profile and profile.photo else '',
            'initial': self.user.username[:1].upper(),
            'profile_url': profile.get_absolute_url() if profile else '',
            'is_online': True,
        }

    @sync_to_async
    def create_message(self, body):
        conversation = Conversation.objects.get(pk=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            body=body,
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        trim_conversation_messages(conversation)
        try:
            profile = self.user.profile
        except ObjectDoesNotExist:
            profile = None
        return {
            'id': message.id,
            'body': message.body,
            'sender_name': self.user.username,
            'sender_avatar_url': profile.photo.url if profile and profile.photo else '',
            'sender_initial': self.user.username[:1].upper(),
            'created_at': friendly_datetime(message.created_at),
        }

    @sync_to_async
    def notify_unread_participants(self):
        conversation = Conversation.objects.prefetch_related('participants').get(pk=self.conversation_id)
        notify_conversation_participants(conversation, exclude_user=self.user)

    @sync_to_async
    def mark_current_conversation_read(self):
        conversation = Conversation.objects.get(pk=self.conversation_id)
        unread_messages = list(
            Message.objects
            .filter(conversation=conversation, read_at__isnull=True)
            .exclude(sender=self.user)
            .values_list('id', flat=True)
        )
        mark_conversation_read(conversation, self.user)
        return unread_messages

    @sync_to_async
    def current_notification_counts(self):
        return notification_counts(self.user)

    async def send_notification_counts(self):
        await self.channel_layer.group_send(
            f'user_{self.user.id}_notifications',
            {
                'type': 'notifications.update',
                'counts': await self.current_notification_counts(),
            },
        )


class NotificationsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'user_{self.user.id}_notifications'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps(await self.current_counts()))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notifications_update(self, event):
        await self.send(text_data=json.dumps(event['counts']))

    @sync_to_async
    def current_counts(self):
        return notification_counts(self.user)
