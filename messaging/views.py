from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import HEALTH_CONTEXT_CHOICES
from accounts.models import Connection
from community.models import Group, GroupMembership

from .chat_rooms import is_chat_conversation, is_chat_group
from .forms import MessageForm
from .models import MESSAGE_MAX_LENGTH, Conversation, Message
from .notifications import (
    mark_conversation_read,
    notify_conversation_participants,
    notify_user,
    unread_count_for_conversation,
)
from .presence import active_user_ids


SPANISH_WEEKDAYS = {
    0: 'lunes',
    1: 'martes',
    2: 'miércoles',
    3: 'jueves',
    4: 'viernes',
    5: 'sábado',
    6: 'domingo',
}

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


def chat_time_label(value):
    if not value:
        return ''

    local_value = timezone.localtime(value)
    today = timezone.localdate()
    value_date = local_value.date()
    days = (today - value_date).days

    if days == 0:
        return local_value.strftime('%H:%M')
    if days == 1:
        return 'ayer'
    if 1 < days < 7:
        return SPANISH_WEEKDAYS[value_date.weekday()]
    return f'{local_value.day}/{local_value.month}/{local_value.strftime("%y")}'


def user_display(user):
    return user.username


def initials_from(text):
    parts = [part for part in text.split() if part]
    if not parts:
        return '?'
    return ''.join(part[0] for part in parts[:2]).upper()


def private_chat_subtitle(profile):
    if not profile:
        return 'Chat privado'
    parts = []
    if profile.age:
        parts.append(f'{profile.age} años')
    if profile.location_label:
        parts.append(profile.location_label)
    return ' · '.join(parts) or 'Chat privado'


def is_community_conversation(conversation):
    return bool(
        conversation
        and (
            (conversation.group and not is_chat_group(conversation.group))
            or conversation.plan
        )
    )


def conversation_is_blocked(conversation, user):
    if conversation.group_id or conversation.plan_id:
        return False
    other_users = [participant for participant in conversation.participants.all() if participant != user]
    if not other_users:
        return False
    other = other_users[0]
    return Connection.objects.filter(
        (Q(requester=user, receiver=other) | Q(requester=other, receiver=user)),
        status=Connection.Status.BLOCKED,
    ).exists()


def conversation_presenter(conversation, current_user):
    message_list = list(conversation.messages.all())
    last_message = message_list[-1] if message_list else None
    other_participants = [participant for participant in conversation.participants.all() if participant != current_user]

    if conversation.group:
        title = conversation.group.name
        subtitle = conversation.group.topic or conversation.group.city or 'Grupo'
        avatar_url = ''
        initials = initials_from(conversation.group.name)
    elif conversation.plan:
        title = conversation.plan.title
        subtitle = conversation.plan.location_label
        avatar_url = ''
        initials = initials_from(conversation.plan.title)
    else:
        names = [user_display(participant) for participant in other_participants]
        title = ', '.join(names) if names else 'Conversación privada'
        other_profile = getattr(other_participants[0], 'profile', None) if other_participants else None
        subtitle = private_chat_subtitle(other_profile)
        avatar_url = other_profile.photo.url if other_profile and other_profile.photo else ''
        initials = initials_from(title)

    if last_message and last_message.body:
        last_body = last_message.body
    elif last_message and last_message.image:
        last_body = 'Imagen'
    else:
        last_body = 'Todavía no hay mensajes.'
    if last_message and last_message.sender == current_user:
        last_body = f'Tu: {last_body}'

    return {
        'conversation': conversation,
        'title': title,
        'subtitle': subtitle,
        'avatar_url': avatar_url,
        'initials': initials,
        'last_message': last_body,
        'time_label': chat_time_label(last_message.created_at if last_message else conversation.updated_at),
        'unread_count': unread_count_for_conversation(conversation, current_user),
    }


@login_required
def inbox(request):
    conversations = request.user.conversations.select_related('group', 'plan').prefetch_related('participants__profile', 'messages')
    conversation_items = [
        conversation_presenter(conversation, request.user)
        for conversation in conversations
        if not is_chat_conversation(conversation) and not is_community_conversation(conversation)
    ]
    return render(request, 'messaging/inbox.html', {'conversation_items': conversation_items})


@login_required
def chat_lobby(request):
    query = (request.GET.get('q') or '').strip()
    rooms = chat_room_options()
    if query:
        normalized_query = query.casefold()
        rooms = [
            room for room in rooms
            if normalized_query in f"{room['title']} {room['description']} {room['kind']}".casefold()
        ]
    return render(request, 'messaging/chat_lobby.html', {
        'query': query,
        'rooms': rooms,
    })


@login_required
def chat_room_enter(request, slug):
    room = get_chat_room(slug)
    if not room:
        raise Http404('Sala no encontrada')

    group_name = room['title'] if room['slug'] == 'general' else f"Chat: {room['title']}"
    group = Group.objects.filter(name=group_name).order_by('pk').first()
    if not group:
        group = Group.objects.create(
            name=group_name,
            description=room['description'],
            city='',
            topic=room['kind'],
            privacy=Group.Privacy.OPEN,
            created_by=request.user,
        )
    GroupMembership.objects.update_or_create(
        group=group,
        user=request.user,
        defaults={'status': GroupMembership.Status.APPROVED},
    )
    conversation, _ = Conversation.objects.get_or_create(group=group)
    conversation.participants.add(request.user)
    return redirect('conversation_detail', pk=conversation.pk)


@login_required
def delete_conversations(request):
    return redirect('inbox')


@login_required
def delete_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    return redirect('conversation_detail', pk=conversation.pk)


@login_required
def conversation_row(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related('group').prefetch_related('participants__profile', 'messages'),
        pk=pk,
        participants=request.user,
    )
    return render(request, 'messaging/_conversation_row.html', {
        'item': conversation_presenter(conversation, request.user),
    })


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related('group', 'plan').prefetch_related('participants__profile', 'messages__sender__profile'),
        pk=pk,
        participants=request.user,
    )
    is_public_chat = is_chat_conversation(conversation)
    is_community_chat = is_community_conversation(conversation)
    if conversation_is_blocked(conversation, request.user):
        return redirect('inbox')
    if request.method == 'POST':
        files = None if (is_public_chat or is_community_chat) else request.FILES
        form = MessageForm(request.POST, files)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            conversation.save()
            notify_conversation_participants(conversation, exclude_user=request.user)
            return redirect('conversation_detail', pk=conversation.pk)
    else:
        form = MessageForm()
    chat_messages = conversation.messages.select_related('sender__profile').order_by('-created_at')
    chat_header = conversation_presenter(conversation, request.user)
    chat_participants = []
    if is_public_chat or is_community_chat:
        active_ids = active_user_ids(conversation.pk)
        participants = conversation.participants.select_related('profile').order_by('username')
        if is_public_chat:
            participants = participants.filter(pk__in=active_ids)
        for participant in participants:
            profile = getattr(participant, 'profile', None)
            details = []
            if profile and profile.age:
                details.append(f'{profile.age} años')
            if profile and profile.location_label:
                details.append(profile.location_label)
            chat_participants.append({
                'user': participant,
                'profile': profile,
                'details': ' · '.join(details) or 'Sin datos de perfil',
                'profile_url': profile.get_absolute_url() if profile else '',
                'is_online': participant.pk in active_ids,
            })
    mark_conversation_read(conversation, request.user)
    notify_user(request.user)
    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'form': form,
        'chat_header': chat_header,
        'is_public_chat': is_public_chat,
        'is_community_chat': is_community_chat,
        'chat_participants': chat_participants,
        'chat_messages': chat_messages,
    })


@login_required
def message_edit(request, pk):
    message = get_object_or_404(
        Message.objects.select_related('conversation__group'),
        pk=pk,
        sender=request.user,
        conversation__participants=request.user,
    )
    if is_chat_conversation(message.conversation):
        return redirect('conversation_detail', pk=message.conversation_id)
    if request.method == 'POST':
        body = (request.POST.get('body') or '').strip()
        if body:
            message.body = body[:MESSAGE_MAX_LENGTH]
            message.edited_at = timezone.now()
            message.save(update_fields=['body', 'edited_at'])
            message.conversation.save()
    return redirect('conversation_detail', pk=message.conversation_id)


@login_required
def message_delete(request, pk):
    message = get_object_or_404(
        Message.objects.select_related('conversation__group'),
        pk=pk,
        sender=request.user,
        conversation__participants=request.user,
    )
    conversation_id = message.conversation_id
    if is_chat_conversation(message.conversation):
        return redirect('conversation_detail', pk=conversation_id)
    if request.method == 'POST':
        if message.image:
            message.image.delete(save=False)
        message.delete()
        conversation = Conversation.objects.filter(pk=conversation_id).first()
        if conversation:
            conversation.save()
    return redirect('conversation_detail', pk=conversation_id)

# Create your views here.
