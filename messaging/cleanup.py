from .models import MESSAGE_KEEP_LIMIT, Message


def trim_conversation_messages(conversation, keep_limit=MESSAGE_KEEP_LIMIT):
    if not conversation or keep_limit <= 0:
        return 0

    message_ids_to_keep = (
        Message.objects
        .filter(conversation=conversation)
        .order_by('-created_at', '-pk')
        .values_list('pk', flat=True)[:keep_limit]
    )
    old_messages = Message.objects.filter(conversation=conversation).exclude(pk__in=list(message_ids_to_keep))
    deleted_count = 0
    for message in old_messages.only('pk', 'image'):
        if message.image:
            message.image.delete(save=False)
        message.delete()
        deleted_count += 1
    return deleted_count
