from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import Connection

from .chat_rooms import is_chat_conversation, is_chat_group
from .models import Conversation, ConversationReadState, Message, PanelNotification


def is_community_conversation(conversation):
    return bool(
        conversation
        and (
            (conversation.group and not is_chat_group(conversation.group))
            or conversation.plan
        )
    )


def unread_message_count(user):
    if not user.is_authenticated:
        return 0

    total = 0
    conversations = (
        user.conversations
        .prefetch_related('read_states')
        .annotate(other_messages=Count('messages', filter=~Q(messages__sender=user)))
    )
    for conversation in conversations:
        if is_chat_conversation(conversation) or is_community_conversation(conversation):
            continue
        state = next(
            (read_state for read_state in conversation.read_states.all() if read_state.user_id == user.id),
            None,
        )
        messages = Message.objects.filter(conversation=conversation).exclude(sender=user)
        if state and state.last_read_at:
            messages = messages.filter(created_at__gt=state.last_read_at)
        total += messages.count()
    return total


def unread_count_for_conversation(conversation, user):
    state = ConversationReadState.objects.filter(conversation=conversation, user=user).first()
    messages = Message.objects.filter(conversation=conversation).exclude(sender=user)
    if state and state.last_read_at:
        messages = messages.filter(created_at__gt=state.last_read_at)
    return messages.count()


def private_message_unread_items(user):
    if not user.is_authenticated:
        return []

    items = []
    conversations = (
        user.conversations
        .select_related('group', 'plan')
        .prefetch_related('participants', 'read_states')
        .order_by('-updated_at')
    )
    for conversation in conversations:
        if is_chat_conversation(conversation) or is_community_conversation(conversation):
            continue
        unread_count = unread_count_for_conversation(conversation, user)
        if not unread_count:
            continue
        other_user = next(
            (participant for participant in conversation.participants.all() if participant.id != user.id),
            None,
        )
        items.append({
            'conversation': conversation,
            'title': other_user.username if other_user else 'Conversación privada',
            'unread_count': unread_count,
        })
    return items


def community_chat_unread_items(user):
    if not user.is_authenticated:
        return []

    items = []
    conversations = (
        user.conversations
        .select_related('group', 'plan')
        .prefetch_related('read_states')
        .order_by('-updated_at')
    )
    for conversation in conversations:
        if not is_community_conversation(conversation):
            continue
        unread_count = unread_count_for_conversation(conversation, user)
        if not unread_count:
            continue
        if conversation.group:
            title = conversation.group.name
            kind = 'Grupo'
        else:
            title = conversation.plan.title
            kind = 'Plan'
        items.append({
            'conversation': conversation,
            'title': title,
            'kind': kind,
            'unread_count': unread_count,
        })
    return items


def pending_connection_count(user):
    if not user.is_authenticated:
        return 0
    return Connection.objects.filter(receiver=user, status=Connection.Status.PENDING).count()


def pending_panel_count(user):
    if not user.is_authenticated:
        return 0

    from community.models import Group, GroupMembership, Plan, PlanAttendance

    moderated_groups = (
        Group.objects
        .filter(Q(created_by=user) | Q(groupmembership__user=user, groupmembership__status=GroupMembership.Status.MODERATOR))
        .distinct()
    )
    moderated_groups = [group for group in moderated_groups if not is_chat_group(group)]
    moderated_plans = (
        Plan.objects
        .filter(
            Q(created_by=user)
            | Q(group__groupmembership__user=user, group__groupmembership__status=GroupMembership.Status.MODERATOR)
        )
        .distinct()
    )
    moderation_requests = (
        GroupMembership.objects
        .filter(group__in=moderated_groups, status=GroupMembership.Status.PENDING)
        .exclude(user=user)
        .count()
    )
    moderation_requests += (
        PlanAttendance.objects
        .filter(plan__in=moderated_plans, status=PlanAttendance.Status.REQUESTED)
        .exclude(user=user)
        .count()
    )
    own_requests = sum(
        1 for membership in GroupMembership.objects.filter(user=user, status=GroupMembership.Status.PENDING).select_related('group')
        if not is_chat_group(membership.group)
    )
    own_requests += PlanAttendance.objects.filter(user=user, status=PlanAttendance.Status.REQUESTED).count()
    unread_panel_notifications = PanelNotification.objects.filter(user=user, is_read=False).count()
    community_chat_messages = sum(item['unread_count'] for item in community_chat_unread_items(user))
    return moderation_requests + own_requests + unread_panel_notifications + community_chat_messages


def notification_counts(user):
    return {
        'messages': unread_message_count(user),
        'connections': pending_connection_count(user),
        'panel': pending_panel_count(user),
    }


def mark_conversation_read(conversation, user):
    now = timezone.now()
    ConversationReadState.objects.update_or_create(
        conversation=conversation,
        user=user,
        defaults={'last_read_at': now},
    )
    Message.objects.filter(
        conversation=conversation,
        read_at__isnull=True,
    ).exclude(sender=user).update(read_at=now)


def notify_user(user, conversation=None):
    if not user or not user.is_authenticated:
        return

    payload = notification_counts(user)
    if conversation:
        if is_chat_conversation(conversation) or is_community_conversation(conversation):
            conversation = None

    if conversation:
        from .views import conversation_presenter

        item = conversation_presenter(conversation, user)
        payload['conversation'] = {
            'id': conversation.id,
            'title': item['title'],
            'subtitle': item['subtitle'],
            'avatar_url': item['avatar_url'],
            'initials': item['initials'],
            'last_message': item['last_message'],
            'time_label': item['time_label'],
            'unread_count': item['unread_count'],
            'url': f'/mensajes/{conversation.id}/',
            'row_url': f'/mensajes/{conversation.id}/fila/',
        }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user.id}_notifications',
        {
            'type': 'notifications.update',
            'counts': payload,
        },
    )


def notify_conversation_participants(conversation, exclude_user=None):
    for participant in conversation.participants.all():
        if exclude_user and participant.id == exclude_user.id:
            continue
        notify_user(participant, conversation=conversation)
