from collections import defaultdict


_active_chat_channels = defaultdict(set)


def join_chat(conversation_id, user_id, channel_name):
    key = (str(conversation_id), int(user_id))
    _active_chat_channels[key].add(channel_name)


def leave_chat(conversation_id, user_id, channel_name):
    key = (str(conversation_id), int(user_id))
    channels = _active_chat_channels.get(key)
    if not channels:
        return True
    channels.discard(channel_name)
    if channels:
        return False
    _active_chat_channels.pop(key, None)
    return True


def active_user_ids(conversation_id):
    conversation_key = str(conversation_id)
    return [
        user_id
        for (active_conversation_id, user_id), channels in _active_chat_channels.items()
        if active_conversation_id == conversation_key and channels
    ]
