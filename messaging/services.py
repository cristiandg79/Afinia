from django.db import transaction
from .models import Conversation, ConversationReadState, Message


def private_conversations_between(user_a, user_b):
    conversations = (
        Conversation.objects
        .filter(group__isnull=True, plan__isnull=True, participants=user_a)
        .filter(participants=user_b)
        .prefetch_related('participants')
    )
    expected_ids = {user_a.id, user_b.id}
    return [
        conversation
        for conversation in conversations
        if {participant.id for participant in conversation.participants.all()} == expected_ids
    ]


def _conversation_priority(conversation):
    messages = list(conversation.messages.all())
    last_message = messages[-1] if messages else None
    has_messages = 1 if last_message else 0
    last_activity = last_message.created_at if last_message else conversation.updated_at
    return (has_messages, last_activity, conversation.updated_at, conversation.pk)


def merge_private_conversations(user_a, user_b):
    conversations = list(
        Conversation.objects
        .filter(pk__in=[conversation.pk for conversation in private_conversations_between(user_a, user_b)])
        .prefetch_related('messages', 'read_states', 'participants')
    )
    if not conversations:
        return None

    primary = max(conversations, key=_conversation_priority)
    duplicates = [conversation for conversation in conversations if conversation.pk != primary.pk]

    if not duplicates:
        return primary

    with transaction.atomic():
        primary.participants.add(user_a, user_b)
        for duplicate in duplicates:
            Message.objects.filter(conversation=duplicate).update(conversation=primary)
            for read_state in duplicate.read_states.all():
                primary_state, _ = ConversationReadState.objects.get_or_create(
                    conversation=primary,
                    user=read_state.user,
                )
                if (
                    read_state.last_read_at
                    and (
                        not primary_state.last_read_at
                        or read_state.last_read_at > primary_state.last_read_at
                    )
                ):
                    primary_state.last_read_at = read_state.last_read_at
                    primary_state.save(update_fields=['last_read_at'])
                read_state.delete()
            duplicate.delete()
        primary.save()

    return primary


def get_or_create_private_conversation(user_a, user_b):
    conversation = merge_private_conversations(user_a, user_b)
    if conversation:
        return conversation

    conversation = Conversation.objects.create()
    conversation.participants.add(user_a, user_b)
    return conversation
