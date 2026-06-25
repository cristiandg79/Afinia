from datetime import timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from community.models import Group, GroupMembership, Plan, PlanAttendance
from messaging.chat_rooms import is_chat_group
from messaging.models import Message, PanelNotification
from messaging.notifications import community_chat_unread_items, private_message_unread_items
from publications.models import Publication, PublicationComment, PublicationPhoto

from .choices import HEALTH_CONTEXT_CHOICES
from .forms import ProfileForm, SignUpForm
from .geolocation import RADIUS_CHOICES, city_coords, clean_radius, distance_km, filter_by_radius, filter_by_user_radius
from .locations import LOCATION_COUNTRY_CHOICES
from .models import BlockedEmail, Connection, DatingAction, Profile, ProfilePhoto
from .permissions import is_site_admin, site_admin_required


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


def extra_photo_slots(form, profile):
    photos = list(profile.extra_photos.all()[:4])
    slots = []
    for index, field_name in enumerate(['extra_photo_1', 'extra_photo_2', 'extra_photo_3', 'extra_photo_4']):
        photo = photos[index] if index < len(photos) else None
        slots.append({
            'number': index + 1,
            'field': form[field_name],
            'photo': photo,
            'input_name': f'replace_extra_photo_{photo.pk}' if photo else field_name,
            'input_id': f'replace-extra-photo-{photo.pk}' if photo else form[field_name].id_for_label,
        })
    return slots


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')


def legal_terms(request):
    return render(request, 'accounts/legal_terms.html')


def suggested_profiles_for(profile, limit=8):
    connection_pairs = (
        Connection.objects
        .filter(Q(requester=profile.user) | Q(receiver=profile.user))
        .values_list('requester_id', 'receiver_id')
    )
    excluded_user_ids = {user_id for pair in connection_pairs for user_id in pair}
    excluded_user_ids.add(profile.user_id)

    candidates = (
        Profile.objects
        .filter(user__is_active=True)
        .exclude(user_id__in=excluded_user_ids)
        .select_related('user')
        .order_by('-updated_at')[:300]
    )
    origin = city_coords(profile.country, profile.city)
    user_health = set(profile.health_context or [])

    def score(candidate):
        candidate_coords = city_coords(candidate.country, candidate.city)
        if origin and candidate_coords:
            distance = distance_km(origin, candidate_coords)
            location_score = max(0, 1000 - distance)
        elif candidate.country == profile.country and candidate.city and profile.city and candidate.city.lower() == profile.city.lower():
            location_score = 850
        elif candidate.country == profile.country:
            location_score = 500
        else:
            location_score = 0

        shared_health = len(user_health.intersection(candidate.health_context or []))
        return (location_score + (shared_health * 120), shared_health, candidate.updated_at)

    return sorted(candidates, key=score, reverse=True)[:limit]


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
    suggested_profiles = suggested_profiles_for(profile)
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
                PlanAttendance.Status.APPROVED,
                PlanAttendance.Status.MODERATOR,
            ],
        )
        .select_related('plan', 'plan__group')
        .order_by('-created_at')
    )
    for attendance in my_plan_attendances:
        is_plan_moderator = attendance.status == PlanAttendance.Status.MODERATOR or attendance.plan.created_by_id == request.user.id
        if attendance.plan.group_id:
            is_plan_moderator = is_plan_moderator or GroupMembership.objects.filter(
                group=attendance.plan.group,
                user=request.user,
                status=GroupMembership.Status.MODERATOR,
            ).exists()
        attendance.panel_role_label = 'Moderador' if is_plan_moderator else 'Miembro'
    panel_notifications = list(
        PanelNotification.objects
        .filter(user=request.user, is_read=False)
        .order_by('-created_at')[:10]
    )
    private_message_notifications = private_message_unread_items(request.user)
    community_chat_notifications = community_chat_unread_items(request.user)
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
        'private_message_notifications': private_message_notifications,
        'community_chat_notifications': community_chat_notifications,
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
            for photo in updated.extra_photos.exclude(pk__in=selected_photo_ids):
                replacement = request.FILES.get(f'replace_extra_photo_{photo.pk}')
                if replacement:
                    old_image_name = photo.image.name
                    photo.image = replacement
                    photo.save(update_fields=['image'])
                    if old_image_name and old_image_name != photo.image.name:
                        photo.image.storage.delete(old_image_name)
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
            'extra_photo_slots': extra_photo_slots(form, profile),
        })
    return render(request, 'accounts/profile_form.html', {
        'form': form,
        'extra_photo_slots': extra_photo_slots(form, profile),
        'is_onboarding': is_onboarding,
        'initial_step': initial_step,
    })


@login_required
def profile_delete(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        if user.email:
            BlockedEmail.objects.get_or_create(email=user.email.lower(), defaults={'user': user, 'reason': 'Baja solicitada por el usuario'})
        user.is_active = False
        user.save(update_fields=['is_active'])
        messages.success(request, 'Tu perfil se ha eliminado.')
        return redirect('home')
    return render(request, 'accounts/profile_delete.html')


@login_required
def profile_detail(request, username):
    profile = get_object_or_404(Profile, user__username=username, user__is_active=True)
    connection = Connection.objects.filter(
        Q(requester=request.user, receiver=profile.user) | Q(requester=profile.user, receiver=request.user)
    ).first()
    return render(request, 'accounts/profile_detail.html', {'profile': profile, 'connection': connection})


def clean_people_filters(data, profile):
    filters = {
        'username': data.get('username', '').strip(),
        'country': data.get('country', profile.country or '').strip(),
        'city': data.get('city', profile.city or '').strip(),
        'radius': clean_radius(data.get('radius', '')),
        'situation': data.get('situation', '').strip(),
    }
    valid_countries = {value for value, _ in LOCATION_COUNTRY_CHOICES}
    valid_situations = {value for value, _ in HEALTH_CONTEXT_CHOICES}
    if filters['country'] not in valid_countries:
        filters['country'] = ''
    if filters['situation'] not in valid_situations:
        filters['situation'] = ''
    return filters


@login_required
def discover(request):
    profiles = Profile.objects.filter(user__is_active=True).exclude(user=request.user)
    pending_connections = (
        Connection.objects
        .filter(receiver=request.user, status=Connection.Status.PENDING)
        .select_related('requester__profile')
        .order_by('-created_at')
    )
    if 'clear' in request.GET:
        request.user.profile.people_preferences = {}
        request.user.profile.save(update_fields=['people_preferences'])
        return redirect('discover')

    saved_filters = request.user.profile.people_preferences or {}
    has_submitted_filters = 'searched' in request.GET
    has_saved_filters = bool(saved_filters.get('searched'))
    if has_submitted_filters:
        filters = clean_people_filters(request.GET, request.user.profile)
        request.user.profile.people_preferences = {**filters, 'searched': True}
        request.user.profile.save(update_fields=['people_preferences'])
    elif has_saved_filters:
        filters = clean_people_filters(saved_filters, request.user.profile)
    else:
        filters = clean_people_filters({}, request.user.profile)

    if filters['username']:
        profiles = profiles.filter(user__username__icontains=filters['username'])
    if filters['country']:
        profiles = profiles.filter(country=filters['country'])
    if filters['city'] and not filters['radius']:
        profiles = profiles.filter(city__icontains=filters['city'])
    if filters['situation']:
        profiles = [profile for profile in profiles if filters['situation'] in profile.health_context]
    if filters['radius']:
        profiles = filter_by_user_radius(profiles, request.user.profile, filters['radius'])
    return render(request, 'accounts/discover.html', {
        'profiles': profiles,
        'username': filters['username'],
        'country': filters['country'],
        'city': filters['city'],
        'radius': filters['radius'],
        'situation': filters['situation'],
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
        'country': data.get('country', profile.country or '').strip(),
        'city': data.get('city', profile.city or '').strip(),
        'radius': clean_radius(data.get('radius', '')),
        'min_age': data.get('min_age', '').strip(),
        'max_age': data.get('max_age', '').strip(),
        'sex': data.get('sex', '').strip(),
        'orientation': data.get('orientation', '').strip(),
        'situation': data.get('situation', '').strip(),
    }
    valid_countries = {value for value, _ in LOCATION_COUNTRY_CHOICES}
    if filters['country'] not in valid_countries:
        filters['country'] = ''
    if filters['sex'] not in ['', Profile.Sex.WOMAN, Profile.Sex.MAN]:
        filters['sex'] = ''
    valid_orientations = {value for value, _ in Profile.Orientation.choices}
    if filters['orientation'] not in valid_orientations:
        filters['orientation'] = ''
    valid_situations = {value for value, _ in HEALTH_CONTEXT_CHOICES}
    if filters['situation'] not in valid_situations:
        filters['situation'] = ''
    if not filters['sex']:
        filters['sex'] = inferred_dating_sex(profile)
    return filters


def profile_wants_dating(profile):
    goals = profile.goals or []
    return isinstance(goals, (list, tuple, set)) and Profile.Goal.DATING in goals


@login_required
def dating_search(request):
    acted_user_ids = set(DatingAction.objects.filter(user=request.user).values_list('target_id', flat=True))
    requested_dating_user_ids = set(
        DatingAction.objects
        .filter(user=request.user, action=DatingAction.Action.LIKE)
        .values_list('target_id', flat=True)
    )
    requested_connection_user_ids = set(
        Connection.objects
        .filter(
            requester=request.user,
            status__in=[
                Connection.Status.PENDING,
                Connection.Status.ACCEPTED,
                Connection.Status.BLOCKED,
            ],
        )
        .values_list('receiver_id', flat=True)
    )
    connected_or_blocked_user_ids = set(
        Connection.objects
        .filter(
            receiver=request.user,
            status__in=[
                Connection.Status.ACCEPTED,
                Connection.Status.BLOCKED,
            ],
        )
        .values_list('requester_id', flat=True)
    )
    hidden_dating_user_ids = (
        requested_dating_user_ids
        | requested_connection_user_ids
        | connected_or_blocked_user_ids
    )
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
        .filter(user__is_active=True)
        .exclude(user=request.user)
        .select_related('user')
        .prefetch_related('extra_photos')
    )
    if should_show_profiles and filters['country']:
        profiles = profiles.filter(country=filters['country'])
    if should_show_profiles and filters['city'] and not filters['radius']:
        profiles = profiles.filter(city__icontains=filters['city'])
    if should_show_profiles and filters['sex']:
        profiles = profiles.filter(sex=filters['sex'])
    if should_show_profiles and filters['orientation']:
        profiles = profiles.filter(orientation=filters['orientation'])
    if should_show_profiles and filters['radius']:
        origin_country = filters['country'] or request.user.profile.country
        origin_city = filters['city'] or request.user.profile.city
        profiles = filter_by_radius(profiles, origin_country, origin_city, filters['radius'])
    if should_show_profiles and filters['situation']:
        profiles = [profile for profile in profiles if filters['situation'] in profile.health_context]

    dating_profiles = [
        profile for profile in profiles
        if profile_wants_dating(profile) and profile.user_id not in hidden_dating_user_ids
    ] if should_show_profiles else []
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
    profiles_to_show = unseen_profiles
    showing_seen_profiles = False
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
        'situation_choices': HEALTH_CONTEXT_CHOICES,
    })


def get_or_create_private_conversation(user_a, user_b):
    from messaging.services import get_or_create_private_conversation as get_or_create_conversation

    return get_or_create_conversation(user_a, user_b)


@login_required
def contact_conversation(request, pk):
    target = get_object_or_404(User, pk=pk, is_active=True)
    if target == request.user:
        messages.info(request, 'No puedes abrir un chat contigo mismo.')
        return redirect('contacts')
    if users_are_blocked(request.user, target):
        messages.info(request, 'No puedes enviar mensajes a un usuario bloqueado.')
        return redirect('contacts')
    is_contact = Connection.objects.filter(
        status=Connection.Status.ACCEPTED
    ).filter(
        Q(requester=request.user, receiver=target) | Q(requester=target, receiver=request.user)
    ).exists()
    if not is_contact:
        messages.info(request, 'Solo puedes escribir a tus contactos.')
        return redirect('contacts')

    conversation = get_or_create_private_conversation(request.user, target)
    return redirect('conversation_detail', pk=conversation.pk)


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
    redirect_url = f'{redirect_url}#perfil-afin'
    if target == request.user or action not in [DatingAction.Action.LIKE, DatingAction.Action.PASS]:
        return redirect(redirect_url)
    if not profile_wants_dating(target.profile):
        messages.info(request, 'Este perfil no busca citas.')
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
            messages.success(request, 'Solicitud para conectar enviada.')
    else:
        messages.info(request, 'Perfil descartado.')

    return redirect(redirect_url)


@login_required
def request_connection(request, pk):
    receiver = get_object_or_404(User, pk=pk)
    next_url = request.GET.get('next') or receiver.profile.get_absolute_url()
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = receiver.profile.get_absolute_url()
    if receiver == request.user:
        messages.info(request, 'Ese eres tú.')
        return redirect('dashboard')
    if users_are_blocked(request.user, receiver):
        messages.info(request, 'No puedes solicitar conectar con un usuario bloqueado.')
        return redirect(next_url)
    connection, created = Connection.objects.get_or_create(requester=request.user, receiver=receiver)
    if next_url.startswith(reverse('dating_search')):
        DatingAction.objects.update_or_create(
            user=request.user,
            target=receiver,
            defaults={'action': DatingAction.Action.LIKE},
        )
    if created:
        from messaging.notifications import notify_user

        notify_user(receiver)
    messages.success(request, 'Solicitud enviada.')
    return redirect(next_url)


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


@login_required
@site_admin_required
def moderation_panel(request):
    def read_offset(param, max_offset=2000):
        try:
            value = int(request.GET.get(param, 0))
        except (TypeError, ValueError):
            value = 0
        return max(0, min(value, max_offset))

    def page_url(param, offset, panel):
        query = request.GET.copy()
        if offset:
            query[param] = str(offset)
        else:
            query.pop(param, None)
        return f'?{query.urlencode()}#{panel}'

    recent_cutoff = timezone.now() - timedelta(days=7)
    page_size = 40
    users_offset = read_offset('usuarios_offset')
    publications_offset = read_offset('muro_offset')
    groups_offset = read_offset('grupos_offset')
    plans_offset = read_offset('planes_offset')
    messages_offset = read_offset('chats_offset')
    photos_offset = read_offset('fotos_offset')
    emails_offset = read_offset('emails_offset')

    users_qs = User.objects.select_related('profile').order_by(Lower('username'))
    publications_qs = (
        Publication.objects
        .filter(created_at__gte=recent_cutoff)
        .select_related('author__profile')
        .prefetch_related('photos')
        .order_by('-created_at')
    )
    publication_photos_qs = (
        PublicationPhoto.objects
        .filter(created_at__gte=recent_cutoff)
        .select_related('publication__author')
        .order_by('-created_at')
    )
    profile_photos_qs = (
        ProfilePhoto.objects
        .filter(created_at__gte=recent_cutoff)
        .select_related('profile__user')
        .order_by('-created_at')
    )
    profile_main_photos_qs = (
        Profile.objects
        .filter(updated_at__gte=recent_cutoff, photo__isnull=False)
        .exclude(photo='')
        .select_related('user')
        .order_by('-updated_at')
    )
    groups_qs = Group.objects.exclude(Q(name='Chat general') | Q(name__startswith='Chat: ')).select_related('created_by').order_by('name')
    plans_qs = Plan.objects.select_related('created_by', 'group').order_by('title')
    messages_qs = (
        Message.objects
        .filter(created_at__gte=recent_cutoff)
        .filter(Q(conversation__group__isnull=False) | Q(conversation__plan__isnull=False))
        .select_related('sender', 'conversation__group', 'conversation__plan')
        .order_by('-created_at')
    )
    blocked_emails_qs = BlockedEmail.objects.select_related('user', 'blocked_by')

    moderation_photos = []
    for photo in publication_photos_qs:
        moderation_photos.append({
            'created_at': photo.created_at,
            'image_url': photo.image.url,
            'label': 'Muro',
            'username': photo.publication.author.username,
            'delete_url': reverse('moderation_delete_publication_photo', args=[photo.pk]),
            'confirm_text': '¿Eliminar esta foto del muro?',
        })
    for profile in profile_main_photos_qs:
        moderation_photos.append({
            'created_at': profile.updated_at,
            'image_url': profile.photo.url,
            'label': 'Perfil principal',
            'username': profile.user.username,
            'delete_url': reverse('moderation_delete_profile_photo', args=[profile.pk]),
            'confirm_text': '¿Eliminar la foto principal de este perfil?',
        })
    for photo in profile_photos_qs:
        moderation_photos.append({
            'created_at': photo.created_at,
            'image_url': photo.image.url,
            'label': 'Perfil',
            'username': photo.profile.user.username,
            'delete_url': reverse('moderation_delete_extra_photo', args=[photo.pk]),
            'confirm_text': '¿Eliminar esta foto del perfil?',
        })
    moderation_photos.sort(key=lambda item: item['created_at'], reverse=True)

    users_count = users_qs.count()
    publications_count = publications_qs.count()
    groups_count = groups_qs.count()
    plans_count = plans_qs.count()
    messages_count = messages_qs.count()
    moderation_photos_count = len(moderation_photos)
    blocked_emails_count = blocked_emails_qs.count()

    return render(request, 'accounts/moderation_panel.html', {
        'users': users_qs[users_offset:users_offset + page_size],
        'publications': publications_qs[publications_offset:publications_offset + page_size],
        'moderation_photos': moderation_photos[photos_offset:photos_offset + page_size],
        'groups': groups_qs[groups_offset:groups_offset + page_size],
        'plans': plans_qs[plans_offset:plans_offset + page_size],
        'messages_list': messages_qs[messages_offset:messages_offset + page_size],
        'blocked_emails': blocked_emails_qs[emails_offset:emails_offset + page_size],
        'active_user_count': User.objects.filter(is_active=True).count(),
        'blocked_email_count': BlockedEmail.objects.count(),
        'moderation_more_links': {
            'usuarios': page_url('usuarios_offset', users_offset + page_size, 'usuarios') if users_count > users_offset + page_size else '',
            'muro': page_url('muro_offset', publications_offset + page_size, 'muro') if publications_count > publications_offset + page_size else '',
            'grupos': page_url('grupos_offset', groups_offset + page_size, 'grupos') if groups_count > groups_offset + page_size else '',
            'planes': page_url('planes_offset', plans_offset + page_size, 'planes') if plans_count > plans_offset + page_size else '',
            'mensajes': page_url('chats_offset', messages_offset + page_size, 'mensajes') if messages_count > messages_offset + page_size else '',
            'fotos': page_url('fotos_offset', photos_offset + page_size, 'fotos') if moderation_photos_count > photos_offset + page_size else '',
            'emails': page_url('emails_offset', emails_offset + page_size, 'emails') if blocked_emails_count > emails_offset + page_size else '',
        },
        'moderation_previous_links': {
            'usuarios': page_url('usuarios_offset', max(users_offset - page_size, 0), 'usuarios') if users_offset else '',
            'muro': page_url('muro_offset', max(publications_offset - page_size, 0), 'muro') if publications_offset else '',
            'grupos': page_url('grupos_offset', max(groups_offset - page_size, 0), 'grupos') if groups_offset else '',
            'planes': page_url('planes_offset', max(plans_offset - page_size, 0), 'planes') if plans_offset else '',
            'mensajes': page_url('chats_offset', max(messages_offset - page_size, 0), 'mensajes') if messages_offset else '',
            'fotos': page_url('fotos_offset', max(photos_offset - page_size, 0), 'fotos') if photos_offset else '',
            'emails': page_url('emails_offset', max(emails_offset - page_size, 0), 'emails') if emails_offset else '',
        },
        'has_moderation_photos': bool(moderation_photos_count),
    })


def redirect_after_moderation(request, fallback='moderation_panel'):
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse(fallback)
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(fallback)
    return redirect(next_url)


@login_required
@site_admin_required
@require_POST
def moderation_delete_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    for photo in publication.photos.all():
        photo.image.delete(save=False)
    publication.delete()
    messages.success(request, 'Publicación eliminada.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_publication_photo(request, pk):
    photo = get_object_or_404(PublicationPhoto, pk=pk)
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, 'Foto del muro eliminada.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_publication_comment(request, pk):
    comment = get_object_or_404(PublicationComment, pk=pk)
    comment.delete()
    messages.success(request, 'Comentario eliminado.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if is_chat_group(group):
        messages.error(request, 'No se puede eliminar una sala de chat base.')
        return redirect_after_moderation(request)
    for plan in group.plans.all():
        plan.delete()
    group.delete()
    messages.success(request, 'Grupo eliminado.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_plan(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    plan.delete()
    messages.success(request, 'Plan eliminado.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    conversation = message.conversation
    if message.image:
        message.image.delete(save=False)
    message.delete()
    conversation.save()
    messages.success(request, 'Mensaje eliminado.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_profile_photo(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if profile.photo:
        profile.photo.delete(save=False)
        profile.photo = None
        profile.save(update_fields=['photo'])
        messages.success(request, 'Foto principal eliminada.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_delete_extra_photo(request, pk):
    photo = get_object_or_404(ProfilePhoto, pk=pk)
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, 'Foto de perfil eliminada.')
    return redirect_after_moderation(request)


@login_required
@site_admin_required
@require_POST
def moderation_block_user(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.error(request, 'No puedes bloquear tu propio usuario administrador.')
        return redirect_after_moderation(request)
    if is_site_admin(target):
        messages.error(request, 'No puedes bloquear otro usuario administrador.')
        return redirect_after_moderation(request)

    blocked_email = target.email.strip().lower() if target.email else ''
    if blocked_email:
        BlockedEmail.objects.update_or_create(
            email=blocked_email,
            defaults={
                'user': target,
                'blocked_by': request.user,
                'reason': 'Usuario bloqueado por moderación',
            },
        )

    deleted_publications = 0
    for publication in target.publications.prefetch_related('photos'):
        for photo in publication.photos.all():
            photo.image.delete(save=False)
        publication.delete()
        deleted_publications += 1

    deleted_comments, _ = target.publication_comments.all().delete()
    target.publication_likes.all().delete()

    affected_conversations = set()
    deleted_messages = 0
    for message in Message.objects.filter(sender=target).select_related('conversation'):
        affected_conversations.add(message.conversation_id)
        if message.image:
            message.image.delete(save=False)
        message.delete()
        deleted_messages += 1

    target.conversation_read_states.all().delete()
    target.conversations.remove(*list(target.conversations.all()))

    for conversation_id in affected_conversations:
        try:
            conversation = Message._meta.get_field('conversation').related_model.objects.get(pk=conversation_id)
            conversation.save()
        except Message._meta.get_field('conversation').related_model.DoesNotExist:
            pass

    target.is_active = False
    target.save(update_fields=['is_active'])

    messages.success(
        request,
        f'Usuario bloqueado. Email conservado y bloqueado. Eliminados {deleted_publications} posts, {deleted_comments} comentarios y {deleted_messages} mensajes.'
    )
    return redirect_after_moderation(request)

# Create your views here.

