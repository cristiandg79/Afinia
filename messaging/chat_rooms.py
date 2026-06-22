from accounts.forms import HEALTH_CONTEXT_CHOICES


def chat_room_options():
    rooms = [
        {
            'slug': 'general',
            'title': 'Chat general',
            'kind': 'General',
            'description': 'Un espacio abierto para hablar, saludar y conocer gente de la comunidad.',
        }
    ]
    for value, label in HEALTH_CONTEXT_CHOICES:
        description = f'Chat para compartir experiencias y conversar sobre {label.lower()}.'
        if value == 'prefer_not_detail':
            description = 'Chat para conversar sin entrar en detalles sobre tu situación personal.'
        rooms.append({
            'slug': value,
            'title': label,
            'kind': 'Situación',
            'description': description,
        })
    return rooms


def get_chat_room(slug):
    for room in chat_room_options():
        if room['slug'] == slug:
            return room
    return None


def chat_group_name(room):
    return room['title'] if room['slug'] == 'general' else f"Chat: {room['title']}"


def is_chat_group(group):
    if not group:
        return False
    return group.name == 'Chat general' or group.name.startswith('Chat: ')


def is_chat_conversation(conversation):
    return bool(conversation and is_chat_group(getattr(conversation, 'group', None)))
