from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from community.models import Group, GroupMembership, Plan, PlanAttendance
from messaging.chat_rooms import is_chat_group
from messaging.models import PanelNotification

from .choices import HEALTH_CONTEXT_CHOICES
from .forms import ProfileForm, SignUpForm
from .geolocation import RADIUS_CHOICES, clean_radius, filter_by_user_radius
from .locations import LOCATION_COUNTRY_CHOICES
from .models import Connection, DatingAction, Profile, ProfilePhoto


PROFILE_FORM_STEPS = {
    'country': 1,
    'city': 1,
    'goals': 2,
    'interests': 3,
    'social_preferences': 4,
    'health_context': 5,
    'bio': 6,
    'sex': 7,
    'orientation': 7,
    'birth_date': 7,
    'height_cm': 7,
    'weight_kg': 7,
    'smoker': 7,
    'photo': 8,
    'extra_photo_1': 8,
    'extra_photo_2': 8,
    'extra_photo_3': 8,
    'extra_photo_4': 8,
}


def first_profile_error_step(form):
    for field_name in form.errors:
        if field_name in PROFILE_FORM_STEPS:
            return PROFILE_FORM_STEPS[field_name]
    return 1


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            Profile.objects.create(
                user=user,
                display_name=user.username,
            )
            login(request, user)
            messages.success(request, 'Cuenta creada. Ahora completa tu perfil a tu ritmo.')
            return redirect('profile_edit')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def dashboard(request):
    profile = request.user.profile
    suggested_profiles = Profile.objects.exclude(user=request.user).order_by('-updated_at')[:6]
    pending_connections = Connection.objects.filter(receiver=request.user, status=Connection.Status.PENDING)
    moderated_groups = (
        Group.objects
        .filter(Q(created_by=request.user) | Q(groupmembership__user=request.user, groupmembership__status=GroupMembership.Status.MODERATOR))
        .distinct()
    )
    moderated_groups = [group for group in moderated_groups if not is_chat_group(group)]
    moderated_plans = (
        Plan.objects
        .filter(
            Q(created_by=request.user)
            | Q(group__groupmembership__user=request.user, group__groupmembership__status=GroupMembership.Status.MODERATOR)
        )
        .distinct()
    )
    pending_group_memberships = (
        GroupMembership.objects
        .filter(group__in=moderated_groups, status=GroupMembership.Status.PENDING)
        .exclude(user=request.user)
        .select_related('group', 'user__profile')
        .order_by('joined_at')
    )
    pending_plan_attendances = (
        PlanAttendance.objects
        .filter(plan__in=moderated_plans, status=PlanAttendance.Status.REQUESTED)
        .exclude(user=request.user)
        .select_related('plan', 'user__profile')
        .order_by('created_at')
    )
    my_group_requests = (
        GroupMembership.objects
        .filter(user=request.user, status=GroupMembership.Status.PENDING)
        .select_related('group')
        .order_by('-joined_at')
    )
    my_group_requests = [membership for membership in my_group_requests if not is_chat_group(membership.group)]
    my_plan_requests = (
        PlanAttendance.objects
        .filter(user=request.user, status=PlanAttendance.Status.REQUESTED)
        .select_related('plan')
        .order_by('-created_at')
    )
    my_group_memberships = (
        GroupMembership.objects
        .filter(
            user=request.user,
            status__in=[
                GroupMembership.Status.PENDING,
                GroupMembership.Status.APPROVED,
                GroupMembership.Status.MODERATOR,
            ],
        )
        .select_related('group')
        .order_by('-joined_at')
    )
    my_group_memberships = [membership for membership in my_group_memberships if not is_chat_group(membership.group)]
    my_plan_attendances = (
        PlanAttendance.objects
        .filter(
            user=request.user,
            status__in=[
                PlanAttendance.Status.REQUESTED,
                PlanAttendance.Status.APPROVED,
            ],
        )
        .select_related('plan')
        .order_by('-created_at')
    )
    panel_notifications = list(
        PanelNotification.objects
        .filter(user=request.user, is_read=False)
        .order_by('-created_at')[:10]
    )
    if panel_notifications:
        PanelNotification.objects.filter(pk__in=[notification.pk for notification in panel_notifications]).update(is_read=True)
    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'suggested_profiles': suggested_profiles,
        'pending_connections': pending_connections,
        'pending_group_memberships': pending_group_memberships,
        'pending_plan_attendances': pending_plan_attendances,
        'my_group_requests': my_group_requests,
        'my_plan_requests': my_plan_requests,
        'my_group_memberships': my_group_memberships,
        'my_plan_attendances': my_plan_attendances,
        'panel_notifications': panel_notifications,
    })


@login_required
def my_profile(request):
    return redirect(request.user.profile.get_absolute_url())


@login_required
def profile_edit(request):
    profile = request.user.profile
    initial_step = 1
    is_onboarding = not profile.onboarding_completed
    if request.method == 'POST':
        old_photo_name = profile.photo.name if profile.photo else ''
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            updated = form.save(commit=False)
            has_new_main_photo = bool(form.cleaned_data.get('photo'))
            updated.onboarding_completed = True
            updated.save()
            if has_new_main_photo and old_photo_name and old_photo_name != updated.photo.name:
                updated.photo.storage.delete(old_photo_name)
            selected_photo_ids = request.POST.getlist('delete_extra_photos')
            if selected_photo_ids:
                for photo in updated.extra_photos.filter(pk__in=selected_photo_ids):
                    photo.image.delete(save=False)
                    photo.delete()
            for field_name in ['extra_photo_1', 'extra_photo_2', 'extra_photo_3', 'extra_photo_4']:
                image = form.cleaned_data.get(field_name)
                if image and updated.extra_photos.count() < 4:
                    ProfilePhoto.objects.create(profile=updated, image=image)
            messages.success(request, 'Perfil actualizado.')
            return redirect('dashboard')
        initial_step = first_profile_error_step(form)
    else:
        form = ProfileForm(instance=profile)
    if not is_onboarding:
        return render(request, 'accounts/profile_edit.html', {
            'form': form,
        })
    return render(request, 'accounts/profile_form.html', {
        'form': form,
        'is_onboarding': is_onboarding,
        'initial_step': initial_step,
    })


@login_required
def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Tu perfil se ha eliminado.')
        return redirect('home')
    return render(request, 'accounts/profile_delete.html')


@login_required
def profile_detail(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    connection = Connection.objects.filter(
        Q(requester=request.user, receiver=profile.user) | Q(requester=profile.user, receiver=request.user)
    ).first()
    return render(request, 'accounts/profile_detail.html', {'profile': profile, 'connection': connection})


@login_required
def discover(request):
    profiles = Profile.objects.exclude(user=request.user)
    pending_connections = (
        Connection.objects
        .filter(receiver=request.user, status=Connection.Status.PENDING)
        .select_related('requester__profile')
        .order_by('-created_at')
    )
    username = request.GET.get('username', '').strip()
    country = request.GET.get('country', '').strip()
    city = request.GET.get('city', '').strip()
    radius = clean_radius(request.GET.get('radius', ''))
    situation = request.GET.get('situation')
    valid_situations = {value for value, _ in HEALTH_CONTEXT_CHOICES}
    if situation not in valid_situations:
        situation = ''
    if username:
        profiles = profiles.filter(user__username__icontains=username)
    if country:
        profiles = profiles.filter(country=country)
    if city:
        profiles = profiles.filter(city__icontains=city)
    if situation:
        profiles = [profile for profile in profiles if situation in profile.health_context]
    if radius:
        profiles = filter_by_user_radius(profiles, request.user.profile, radius)
    return render(request, 'accounts/discover.html', {
        'profiles': profiles,
        'username': username,
        'country': country,
        'city': city,
        'radius': radius,
        'situation': situation,
        'situation_choices': HEALTH_CONTEXT_CHOICES,
        'country_choices': LOCATION_COUNTRY_CHOICES,
        'radius_choices': RADIUS_CHOICES,
        'pending_connections': pending_connections,
    })


@login_required
def contacts(request):
    connections = (
        Connection.objects
        .filter(status=Connection.Status.ACCEPTED)
        .filter(Q(requester=request.user) | Q(receiver=request.user))
        .select_related('requester__profile', 'receiver__profile')
        .order_by('-updated_at')
    )
    contact_items = []
    for connection in connections:
        contact_user = connection.receiver if connection.requester == request.user else connection.requester
        contact_items.append({
            'connection': connection,
            'user': contact_user,
            'profile': contact_user.profile,
        })
    blocked_connections = (
        Connection.objects
        .filter(requester=request.user, status=Connection.Status.BLOCKED)
        .select_related('receiver__profile')
        .order_by('-updated_at')
    )
    blocked_items = [
        {
            'connection': connection,
            'user': connection.receiver,
            'profile': connection.receiver.profile,
        }
        for connection in blocked_connections
    ]
    return render(request, 'accounts/contacts.html', {
        'contact_items': contact_items,
        'blocked_items': blocked_items,
    })


def inferred_dating_sex(profile):
    if profile.orientation == Profile.Orientation.HETEROSEXUAL:
        if profile.sex == Profile.Sex.WOMAN:
            return Profile.Sex.MAN
        if profile.sex == Profile.Sex.MAN:
            return Profile.Sex.WOMAN
    if profile.orientation == Profile.Orientation.HOMOSEXUAL:
        if profile.sex in [Profile.Sex.WOMAN, Profile.Sex.MAN]:
            return profile.sex
    return ''


def clean_dating_filters(data, profile):
    filters = {
        'country': data.get('country', '').strip(),
        'city': data.get('city', '').strip(),
        'radius': clean_radius(data.get('radius', '')),
        'min_age': data.get('min_age', '').strip(),
        'max_age': data.get('max_age', '').strip(),
        'sex': data.get('sex', '').strip(),
        'orientation': data.get('orientation', '').strip(),
    }
    valid_countries = {value for value, _ in LOCATION_COUNTRY_CHOICES}
    if filters['country'] not in valid_countries:
        filters['country'] = ''
    if filters['sex'] not in ['', Profile.Sex.WOMAN, Profile.Sex.MAN]:
        filters['sex'] = ''
    valid_orientations = {value for value, _ in Profile.Orientation.choices}
    if filters['orientation'] not in valid_orientations:
        filters['orientation'] = ''
    if not filters['sex']:
        filters['sex'] = inferred_dating_sex(profile)
    return filters


@login_required
def dating_search(request):
    acted_user_ids = set(DatingAction.objects.filter(user=request.user).values_list('target_id', flat=True))
    if 'clear' in request.GET:
        request.user.profile.dating_preferences = {}
        request.user.profile.save(update_fields=['dating_preferences'])
        return redirect('dating_search')
    saved_filters = request.user.profile.dating_preferences or {}
    has_submitted_filters = 'searched' in request.GET
    has_saved_filters = bool(saved_filters.get('searched'))
    if has_submitted_filters:
        filters = clean_dating_filters(request.GET, request.user.profile)
        request.user.profile.dating_preferences = {**filters, 'searched': True}
        request.user.profile.save(update_fields=['dating_preferences'])
    elif has_saved_filters:
        filters = clean_dating_filters(saved_filters, request.user.profile)
    else:
        filters = clean_dating_filters({}, request.user.profile)

    should_show_profiles = has_submitted_filters or has_saved_filters
    profiles = (
        Profile.objects
        .exclude(user=request.user)
        .select_related('user')
        .prefetch_related('extra_photos')
    )
    if should_show_profiles and filters['country']:
        profiles = profiles.filter(country=filters['country'])
    if should_show_profiles and filters['city']:
        profiles = profiles.filter(city__icontains=filters['city'])
    if should_show_profiles and filters['radius']:
        profiles = filter_by_user_radius(profiles, request.user.profile, filters['radius'])
    if should_show_profiles and filters['sex']:
        profiles = profiles.filter(sex=filters['sex'])
    if should_show_profiles and filters['orientation']:
        profiles = profiles.filter(orientation=filters['orientation'])

    dating_profiles = [profile for profile in profiles if 'dating' in profile.goals] if should_show_profiles else []
    min_age = int(filters['min_age']) if filters['min_age'].isdigit() else None
    max_age = int(filters['max_age']) if filters['max_age'].isdigit() else None
    if min_age is not None or max_age is not None:
        dating_profiles = [
            profile for profile in dating_profiles
            if profile.age is not None
            and (min_age is None or profile.age >= min_age)
            and (max_age is None or profile.age <= max_age)
        ]
    unseen_profiles = [profile for profile in dating_profiles if profile.user_id not in acted_user_ids]
    profiles_to_show = unseen_profiles or dating_profiles
    showing_seen_profiles = bool(dating_profiles and not unseen_profiles)
    current_profile = profiles_to_show[0] if profiles_to_show else None
    querystring = request.GET.urlencode()
    if not querystring and has_saved_filters:
        querystring = urlencode({'searched': '1', **{key: value for key, value in filters.items() if value}})
    return render(request, 'accounts/dating_search.html', {
        'profile': current_profile,
        'remaining_count': len(profiles_to_show),
        'filters': filters,
        'should_show_profiles': should_show_profiles,
        'showing_seen_profiles': showing_seen_profiles,
        'querystring': querystring,
        'country_choices': LOCATION_COUNTRY_CHOICES,
        'radius_choices': RADIUS_CHOICES,
        'sex_choices': [
            ('', 'Cualquier perfil'),
            (Profile.Sex.WOMAN, 'Mujeres'),
            (Profile.Sex.MAN, 'Hombres'),
        ],
        'orientation_choices': [('', 'Cualquier orientación'), *Profile.Orientation.choices],
    })


def get_or_create_private_conversation(user_a, user_b):
    from messaging.models import Conversation

    conversation = (
        Conversation.objects
        .filter(group__isnull=True, plan__isnull=True, participants=user_a)
        .filter(participants=user_b)
        .annotate(participant_count=Count('participants'))
        .filter(participant_count=2)
        .first()
    )
    if conversation:
        return conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(user_a, user_b)
    return conversation


def users_are_blocked(user_a, user_b):
    return Connection.objects.filter(
        Q(requester=user_a, receiver=user_b, status=Connection.Status.BLOCKED)
        | Q(requester=user_b, receiver=user_a, status=Connection.Status.BLOCKED)
    ).exists()


@login_required
def dating_action(request, pk, action):
    target = get_object_or_404(User, pk=pk)
    querystring = request.GET.urlencode()
    redirect_url = reverse('dating_search')
    if querystring:
        redirect_url = f'{redirect_url}?{querystring}'
    if target == request.user or action not in [DatingAction.Action.LIKE, DatingAction.Action.PASS]:
        return redirect(redirect_url)
    if users_are_blocked(request.user, target):
        messages.info(request, 'No puedes interactuar con un usuario bloqueado.')
        return redirect(redirect_url)

    DatingAction.objects.update_or_create(
        user=request.user,
        target=target,
        defaults={'action': action},
    )

    if action == DatingAction.Action.LIKE:
        reverse_like = DatingAction.objects.filter(
            user=target,
            target=request.user,
            action=DatingAction.Action.LIKE,
        ).exists()
        connection = Connection.objects.filter(
            Q(requester=request.user, receiver=target) | Q(requester=target, receiver=request.user)
        ).first()
        if not connection:
            connection = Connection.objects.create(requester=request.user, receiver=target)
        if reverse_like:
            connection.status = Connection.Status.ACCEPTED
            connection.save()
            get_or_create_private_conversation(request.user, target)
            messages.success(request, 'Hay conexión mutua. Ya podéis hablar.')
        else:
            from messaging.notifications import notify_user

            notify_user(target)
            messages.success(request, 'Interés enviado.')
    else:
        messages.info(request, 'Perfil descartado.')

    return redirect(redirect_url)


@login_required
def request_connection(request, pk):
    receiver = get_object_or_404(User, pk=pk)
    if receiver == request.user:
        messages.info(request, 'Ese eres tú.')
        return redirect('dashboard')
    if users_are_blocked(request.user, receiver):
        messages.info(request, 'No puedes solicitar conectar con un usuario bloqueado.')
        return redirect(receiver.profile.get_absolute_url())
    connection, created = Connection.objects.get_or_create(requester=request.user, receiver=receiver)
    if created:
        from messaging.notifications import notify_user

        notify_user(receiver)
    messages.success(request, 'Solicitud enviada.')
    return redirect(receiver.profile.get_absolute_url())


@login_required
def respond_connection(request, pk, status):
    connection = get_object_or_404(Connection, pk=pk, receiver=request.user)
    next_url = request.GET.get('next') or 'dashboard'
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'dashboard'
    if status in [Connection.Status.ACCEPTED, Connection.Status.DECLINED, Connection.Status.BLOCKED]:
        connection.status = status
        connection.save()
        if status == Connection.Status.ACCEPTED:
            get_or_create_private_conversation(connection.requester, connection.receiver)
            PanelNotification.objects.create(
                user=connection.requester,
                title='Solicitud aceptada',
                body=f'{connection.receiver.username} ha aceptado tu solicitud para conectar.',
                url=connection.receiver.profile.get_absolute_url(),
            )
        from messaging.notifications import notify_user

        notify_user(connection.requester)
        messages.success(request, 'Solicitud actualizada.')
    return redirect(next_url)


@login_required
def block_contact(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.info(request, 'No puedes bloquearte a ti mismo.')
        return redirect('contacts')
    connection = Connection.objects.filter(
        Q(requester=request.user, receiver=target) | Q(requester=target, receiver=request.user)
    ).first()
    if connection:
        connection.requester = request.user
        connection.receiver = target
        connection.status = Connection.Status.BLOCKED
        connection.save()
    else:
        Connection.objects.create(requester=request.user, receiver=target, status=Connection.Status.BLOCKED)

    from messaging.models import Conversation

    private_conversations = (
        Conversation.objects
        .filter(group__isnull=True, plan__isnull=True, participants=request.user)
        .filter(participants=target)
    )
    for conversation in private_conversations:
        conversation.participants.remove(request.user, target)
    messages.success(request, 'Usuario bloqueado.')
    return redirect('contacts')


@login_required
def delete_contact(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.info(request, 'No puedes eliminarte de tus contactos.')
        return redirect('contacts')

    deleted_count, _ = (
        Connection.objects
        .filter(status=Connection.Status.ACCEPTED)
        .filter(Q(requester=request.user, receiver=target) | Q(requester=target, receiver=request.user))
        .delete()
    )
    if deleted_count:
        messages.success(request, 'Contacto eliminado.')
    else:
        messages.info(request, 'Ese usuario no estaba en tus contactos.')
    return redirect('contacts')


@login_required
def unblock_contact(request, pk):
    target = get_object_or_404(User, pk=pk)
    Connection.objects.filter(requester=request.user, receiver=target, status=Connection.Status.BLOCKED).delete()
    messages.success(request, 'Usuario desbloqueado.')
    return redirect('contacts')

# Create your views here.
