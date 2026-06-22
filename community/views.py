from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.geolocation import RADIUS_CHOICES, clean_radius, filter_by_user_radius
from accounts.locations import LOCATION_COUNTRY_CHOICES

from .forms import GroupForm, PlanForm
from .models import Group, GroupMembership, Plan, PlanAttendance


def notify_panel_users(users):
    from messaging.notifications import notify_user

    seen = set()
    for user in users:
        if not user or user.id in seen:
            continue
        seen.add(user.id)
        notify_user(user)


def create_panel_notification(user, title, body, url=''):
    from messaging.models import PanelNotification

    return PanelNotification.objects.create(
        user=user,
        title=title,
        body=body,
        url=url,
    )


def sync_group_conversation(group):
    from messaging.models import Conversation

    conversation, _ = Conversation.objects.get_or_create(group=group)
    user_ids = GroupMembership.objects.filter(
        group=group,
        status__in=[GroupMembership.Status.APPROVED, GroupMembership.Status.MODERATOR],
    ).values_list('user_id', flat=True)
    conversation.participants.set(User.objects.filter(pk__in=user_ids))
    return conversation


def sync_plan_conversation(plan):
    from messaging.models import Conversation

    conversation, _ = Conversation.objects.get_or_create(plan=plan)
    user_ids = PlanAttendance.objects.filter(
        plan=plan,
        status__in=[PlanAttendance.Status.APPROVED, PlanAttendance.Status.MODERATOR],
    ).values_list('user_id', flat=True)
    conversation.participants.set(User.objects.filter(pk__in=user_ids))
    return conversation


def is_group_moderator(group, user):
    return (
        group.created_by_id == user.id
        or GroupMembership.objects.filter(
            group=group,
            user=user,
            status=GroupMembership.Status.MODERATOR,
        ).exists()
    )


def group_moderator_users(group):
    moderator_ids = set(
        GroupMembership.objects
        .filter(group=group, status=GroupMembership.Status.MODERATOR)
        .values_list('user_id', flat=True)
    )
    moderator_ids.add(group.created_by_id)
    return User.objects.filter(pk__in=moderator_ids)


def group_member_users(group):
    member_ids = set(
        GroupMembership.objects
        .filter(group=group, status__in=[GroupMembership.Status.APPROVED, GroupMembership.Status.MODERATOR])
        .values_list('user_id', flat=True)
    )
    member_ids.add(group.created_by_id)
    return User.objects.filter(pk__in=member_ids)


def is_group_member(group, user):
    return (
        group.created_by_id == user.id
        or GroupMembership.objects.filter(
            group=group,
            user=user,
            status__in=[GroupMembership.Status.APPROVED, GroupMembership.Status.MODERATOR],
        ).exists()
    )


def moderated_plans_for(user):
    return (
        Plan.objects
        .filter(
            Q(created_by=user)
            | Q(group__groupmembership__user=user, group__groupmembership__status=GroupMembership.Status.MODERATOR)
        )
        .distinct()
    )


def is_plan_moderator(plan, user):
    if plan.created_by_id == user.id:
        return True
    if PlanAttendance.objects.filter(
        plan=plan,
        user=user,
        status=PlanAttendance.Status.MODERATOR,
    ).exists():
        return True
    if not plan.group_id:
        return False
    return GroupMembership.objects.filter(
        group=plan.group,
        user=user,
        status=GroupMembership.Status.MODERATOR,
    ).exists()


def plan_moderator_users(plan):
    moderator_ids = {plan.created_by_id}
    moderator_ids.update(
        PlanAttendance.objects
        .filter(plan=plan, status=PlanAttendance.Status.MODERATOR)
        .values_list('user_id', flat=True)
    )
    if plan.group_id:
        moderator_ids.update(
            GroupMembership.objects
            .filter(group=plan.group, status=GroupMembership.Status.MODERATOR)
            .values_list('user_id', flat=True)
        )
    return User.objects.filter(pk__in=moderator_ids)


def can_view_plan(plan, user):
    return not plan.group_id or is_group_member(plan.group, user)


@login_required
def group_list(request):
    groups = Group.objects.exclude(Q(name='Chat general') | Q(name__startswith='Chat: ')).order_by('-created_at')
    title_query = request.GET.get('q', '').strip()
    country_query = request.GET.get('country', '').strip()
    city_query = request.GET.get('city', '').strip()
    radius_query = clean_radius(request.GET.get('radius', ''))
    if title_query:
        groups = groups.filter(name__icontains=title_query)
    if country_query:
        groups = groups.filter(country=country_query)
    if city_query:
        groups = groups.filter(city__icontains=city_query)
    if radius_query:
        groups = filter_by_user_radius(groups, request.user.profile, radius_query)
    return render(request, 'community/group_list.html', {
        'groups': groups,
        'title_query': title_query,
        'country_query': country_query,
        'city_query': city_query,
        'radius_query': radius_query,
        'country_choices': LOCATION_COUNTRY_CHOICES,
        'radius_choices': RADIUS_CHOICES,
    })


@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    is_moderator = is_group_moderator(group, request.user)
    members = (
        GroupMembership.objects
        .filter(group=group, status__in=[GroupMembership.Status.APPROVED, GroupMembership.Status.MODERATOR])
        .select_related('user__profile')
        .order_by('user__username')
    )
    pending_memberships = (
        GroupMembership.objects
        .filter(group=group, status=GroupMembership.Status.PENDING)
        .exclude(user=request.user)
        .select_related('user__profile')
        .order_by('joined_at')
    ) if is_moderator else []
    group_chat = None
    if membership and membership.status in [GroupMembership.Status.APPROVED, GroupMembership.Status.MODERATOR]:
        group_chat = sync_group_conversation(group)
    can_assign_moderators = members.count() > 1
    return render(request, 'community/group_detail.html', {
        'group': group,
        'membership': membership,
        'is_moderator': is_moderator,
        'members': members,
        'pending_memberships': pending_memberships,
        'group_chat': group_chat,
        'can_assign_moderators': can_assign_moderators,
    })


@login_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupMembership.objects.create(group=group, user=request.user, status=GroupMembership.Status.MODERATOR)
            messages.success(request, 'Grupo creado.')
            return redirect(group.get_absolute_url())
    else:
        form = GroupForm()
    return render(request, 'community/group_form.html', {'form': form})


@login_required
def group_join(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if is_group_moderator(group, request.user):
        messages.info(request, 'Ya moderas este grupo.')
        return redirect(group.get_absolute_url())
    status = GroupMembership.Status.APPROVED if group.privacy == Group.Privacy.OPEN else GroupMembership.Status.PENDING
    membership, created = GroupMembership.objects.get_or_create(group=group, user=request.user, defaults={'status': status})
    if created or membership.status == GroupMembership.Status.PENDING:
        notify_panel_users([request.user, *group_moderator_users(group)])
    messages.success(request, 'Solicitud registrada.')
    return redirect(group.get_absolute_url())


@login_required
def group_leave(request, pk):
    group = get_object_or_404(Group, pk=pk)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if group.created_by_id == request.user.id:
        messages.info(request, 'No puedes salir de un grupo que has creado.')
        return redirect(group.get_absolute_url())
    if membership:
        membership.delete()
        sync_group_conversation(group)
        notify_panel_users([request.user, *group_moderator_users(group)])
        messages.success(request, 'Has salido del grupo.')
    else:
        messages.info(request, 'No estabas en este grupo.')
    return redirect(group.get_absolute_url())


@login_required
def group_remove_member(request, pk, user_pk):
    group = get_object_or_404(Group, pk=pk)
    member = get_object_or_404(User, pk=user_pk)
    if not is_group_moderator(group, request.user):
        messages.error(request, 'No puedes gestionar este grupo.')
        return redirect(group.get_absolute_url())
    if member == request.user or member.id == group.created_by_id:
        messages.info(request, 'No puedes expulsar a esta persona del grupo.')
        return redirect(group.get_absolute_url())
    if is_group_moderator(group, member):
        messages.info(request, 'No puedes expulsar a una persona moderadora del grupo.')
        return redirect(group.get_absolute_url())
    membership = GroupMembership.objects.filter(group=group, user=member).first()
    if membership:
        membership.delete()
        sync_group_conversation(group)
        create_panel_notification(
            member,
            'Has salido de un grupo',
            f'Un moderador te ha eliminado del grupo {group.name}.',
            group.get_absolute_url(),
        )
        notify_panel_users([member, request.user, *group_moderator_users(group)])
        messages.success(request, 'Usuario eliminado del grupo.')
    return redirect(group.get_absolute_url())


@login_required
def group_make_moderator(request, pk, user_pk):
    group = get_object_or_404(Group, pk=pk)
    member = get_object_or_404(User, pk=user_pk)
    if request.method != 'POST':
        return redirect(group.get_absolute_url())
    if not is_group_moderator(group, request.user):
        messages.error(request, 'No puedes gestionar este grupo.')
        return redirect(group.get_absolute_url())
    if member.id == group.created_by_id:
        messages.info(request, 'La persona que creó el grupo ya modera este grupo.')
        return redirect(group.get_absolute_url())
    membership = GroupMembership.objects.filter(
        group=group,
        user=member,
        status=GroupMembership.Status.APPROVED,
    ).first()
    if not membership:
        messages.info(request, 'Solo puedes hacer moderador a un miembro del grupo.')
        return redirect(group.get_absolute_url())

    membership.status = GroupMembership.Status.MODERATOR
    membership.save(update_fields=['status'])
    create_panel_notification(
        member,
        'Ahora eres moderador',
        f'Te han cambiado a moderador del grupo {group.name}.',
        group.get_absolute_url(),
    )
    notify_panel_users([member, request.user, *group_moderator_users(group)])
    messages.success(request, f'{member.username} ahora es moderador del grupo.')
    return redirect(group.get_absolute_url())


@login_required
def group_membership_response(request, pk, status):
    membership = get_object_or_404(GroupMembership.objects.select_related('group'), pk=pk)
    if not is_group_moderator(membership.group, request.user):
        messages.error(request, 'No puedes gestionar solicitudes de este grupo.')
        return redirect('group_detail', pk=membership.group_id)
    if status not in [GroupMembership.Status.APPROVED, GroupMembership.Status.DECLINED]:
        messages.error(request, 'Respuesta no válida.')
        return redirect('group_detail', pk=membership.group_id)
    membership.status = status
    membership.save(update_fields=['status'])
    if status == GroupMembership.Status.APPROVED:
        sync_group_conversation(membership.group)
        create_panel_notification(
            membership.user,
            'Solicitud de grupo aceptada',
            f'Te han aceptado en el grupo {membership.group.name}.',
            membership.group.get_absolute_url(),
        )
    else:
        create_panel_notification(
            membership.user,
            'Solicitud de grupo rechazada',
            f'Tu solicitud para unirte a {membership.group.name} ha sido rechazada.',
            membership.group.get_absolute_url(),
        )
    notify_panel_users([request.user, membership.user, *group_moderator_users(membership.group)])
    messages.success(request, 'Solicitud de grupo actualizada.')
    return redirect('group_detail', pk=membership.group_id)


@login_required
def plan_list(request):
    plans = (
        Plan.objects
        .select_related('group', 'created_by')
        .filter(
            Q(group__isnull=True)
            | Q(group__created_by=request.user)
            | Q(
                group__groupmembership__user=request.user,
                group__groupmembership__status__in=[
                    GroupMembership.Status.APPROVED,
                    GroupMembership.Status.MODERATOR,
                ],
            )
        )
        .distinct()
        .order_by('-created_at')
    )
    title_query = request.GET.get('q', '').strip()
    country_query = request.GET.get('country', '').strip()
    city_query = request.GET.get('city', '').strip()
    radius_query = clean_radius(request.GET.get('radius', ''))
    if title_query:
        plans = plans.filter(title__icontains=title_query)
    if country_query:
        plans = plans.filter(country=country_query)
    if city_query:
        plans = plans.filter(city__icontains=city_query)
    if radius_query:
        plans = filter_by_user_radius(plans, request.user.profile, radius_query)
    return render(request, 'community/plan_list.html', {
        'plans': plans,
        'title_query': title_query,
        'country_query': country_query,
        'city_query': city_query,
        'radius_query': radius_query,
        'country_choices': LOCATION_COUNTRY_CHOICES,
        'radius_choices': RADIUS_CHOICES,
    })


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(Plan.objects.select_related('group', 'created_by'), pk=pk)
    if not can_view_plan(plan, request.user):
        messages.error(request, 'Este plan es privado para las personas del grupo.')
        return redirect('plan_list')
    is_moderator = is_plan_moderator(plan, request.user)
    if is_moderator:
        attendance, _ = PlanAttendance.objects.get_or_create(
            plan=plan,
            user=request.user,
            defaults={'status': PlanAttendance.Status.APPROVED},
        )
    else:
        attendance = PlanAttendance.objects.filter(plan=plan, user=request.user).first()
    attendees = (
        PlanAttendance.objects
        .filter(plan=plan, status__in=[PlanAttendance.Status.APPROVED, PlanAttendance.Status.MODERATOR])
        .select_related('user__profile')
        .order_by('user__username')
    )
    pending_attendances = (
        PlanAttendance.objects
        .filter(plan=plan, status=PlanAttendance.Status.REQUESTED)
        .exclude(user=request.user)
        .select_related('user__profile')
        .order_by('created_at')
    ) if is_moderator else []
    plan_chat = None
    if attendance and attendance.status in [PlanAttendance.Status.APPROVED, PlanAttendance.Status.MODERATOR]:
        plan_chat = sync_plan_conversation(plan)
    for attendee in attendees:
        attendee.is_plan_moderator = is_plan_moderator(plan, attendee.user)
    return render(request, 'community/plan_detail.html', {
        'plan': plan,
        'attendance': attendance,
        'is_moderator': is_moderator,
        'attendees': attendees,
        'pending_attendances': pending_attendances,
        'plan_chat': plan_chat,
    })


@login_required
def plan_create(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()
            PlanAttendance.objects.get_or_create(
                plan=plan,
                user=request.user,
                defaults={'status': PlanAttendance.Status.APPROVED},
            )
            sync_plan_conversation(plan)
            messages.success(request, 'Plan creado.')
            return redirect('plan_detail', pk=plan.pk)
    else:
        form = PlanForm()
    return render(request, 'community/plan_form.html', {'form': form})


@login_required
def group_plan_create(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if not is_group_moderator(group, request.user):
        messages.error(request, 'Solo los moderadores del grupo pueden crear planes de grupo.')
        return redirect(group.get_absolute_url())

    if request.method == 'POST':
        form = PlanForm(request.POST, group_plan=True)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.group = group
            plan.created_by = request.user
            plan.capacity = 0
            plan.save()
            PlanAttendance.objects.get_or_create(
                plan=plan,
                user=request.user,
                defaults={'status': PlanAttendance.Status.APPROVED},
            )
            sync_plan_conversation(plan)
            group_chat = sync_group_conversation(group)

            from messaging.models import Message

            plan_url = reverse('plan_detail', kwargs={'pk': plan.pk})
            Message.objects.create(
                conversation=group_chat,
                sender=request.user,
                body=f'Nuevo plan de grupo: {plan.title}\n{request.build_absolute_uri(plan_url)}',
            )
            group_chat.save()

            panel_users = [member for member in group_member_users(group) if member.id != request.user.id]
            for member in panel_users:
                create_panel_notification(
                    member,
                    'Nuevo plan de grupo',
                    f'{request.user.username} ha creado el plan {plan.title} en {group.name}.',
                    plan_url,
                )
            notify_panel_users([request.user, *panel_users])
            messages.success(request, 'Plan de grupo creado.')
            return redirect('plan_detail', pk=plan.pk)
    else:
        form = PlanForm(initial={
            'country': group.country,
            'city': group.city,
        }, group_plan=True)
    return render(request, 'community/plan_form.html', {
        'form': form,
        'group': group,
    })


@login_required
def plan_join(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if not can_view_plan(plan, request.user):
        messages.error(request, 'Este plan es privado para las personas del grupo.')
        return redirect('plan_list')
    if is_plan_moderator(plan, request.user):
        PlanAttendance.objects.get_or_create(
            plan=plan,
            user=request.user,
            defaults={'status': PlanAttendance.Status.APPROVED},
        )
        messages.info(request, 'Ya moderas este plan.')
        return redirect('plan_detail', pk=plan.pk)
    attendance, created = PlanAttendance.objects.get_or_create(plan=plan, user=request.user)
    if created or attendance.status == PlanAttendance.Status.REQUESTED:
        notify_panel_users([request.user, *plan_moderator_users(plan)])
    messages.success(request, 'Solicitud para el plan registrada.')
    return redirect('plan_detail', pk=plan.pk)


@login_required
def plan_leave(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if plan.created_by_id == request.user.id:
        messages.info(request, 'No puedes salir de un plan que has creado.')
        return redirect('plan_detail', pk=plan.pk)
    attendance = PlanAttendance.objects.filter(plan=plan, user=request.user).first()
    if attendance:
        attendance.delete()
        sync_plan_conversation(plan)
        notify_panel_users([request.user, *plan_moderator_users(plan)])
        messages.success(request, 'Has salido del plan.')
    else:
        messages.info(request, 'No estabas apuntado a este plan.')
    return redirect('plan_detail', pk=plan.pk)


@login_required
def plan_remove_attendee(request, pk, user_pk):
    plan = get_object_or_404(Plan, pk=pk)
    attendee = get_object_or_404(User, pk=user_pk)
    if not is_plan_moderator(plan, request.user):
        messages.error(request, 'No puedes gestionar este plan.')
        return redirect('plan_detail', pk=plan.pk)
    if attendee == request.user or attendee.id == plan.created_by_id:
        messages.info(request, 'No puedes expulsar a esta persona del plan.')
        return redirect('plan_detail', pk=plan.pk)
    if is_plan_moderator(plan, attendee):
        messages.info(request, 'No puedes expulsar a una persona moderadora del plan.')
        return redirect('plan_detail', pk=plan.pk)
    attendance = PlanAttendance.objects.filter(plan=plan, user=attendee).first()
    if attendance:
        attendance.delete()
        sync_plan_conversation(plan)
        create_panel_notification(
            attendee,
            'Has salido de un plan',
            f'Un moderador te ha eliminado del plan {plan.title}.',
            reverse('plan_detail', kwargs={'pk': plan.pk}),
        )
        notify_panel_users([attendee, request.user, *plan_moderator_users(plan)])
        messages.success(request, 'Usuario eliminado del plan.')
    return redirect('plan_detail', pk=plan.pk)


@login_required
def plan_make_moderator(request, pk, user_pk):
    plan = get_object_or_404(Plan, pk=pk)
    member = get_object_or_404(User, pk=user_pk)
    if request.method != 'POST':
        return redirect('plan_detail', pk=plan.pk)
    if not is_plan_moderator(plan, request.user):
        messages.error(request, 'No puedes gestionar este plan.')
        return redirect('plan_detail', pk=plan.pk)
    if member.id == plan.created_by_id:
        messages.info(request, 'La persona que creó el plan ya modera este plan.')
        return redirect('plan_detail', pk=plan.pk)
    attendance = PlanAttendance.objects.filter(
        plan=plan,
        user=member,
        status=PlanAttendance.Status.APPROVED,
    ).first()
    if not attendance:
        messages.info(request, 'Solo puedes hacer moderador a una persona apuntada al plan.')
        return redirect('plan_detail', pk=plan.pk)

    attendance.status = PlanAttendance.Status.MODERATOR
    attendance.save(update_fields=['status'])
    sync_plan_conversation(plan)
    create_panel_notification(
        member,
        'Ahora eres moderador',
        f'Te han cambiado a moderador del plan {plan.title}.',
        reverse('plan_detail', kwargs={'pk': plan.pk}),
    )
    notify_panel_users([member, request.user, *plan_moderator_users(plan)])
    messages.success(request, f'{member.username} ahora es moderador del plan.')
    return redirect('plan_detail', pk=plan.pk)


@login_required
def plan_attendance_response(request, pk, status):
    attendance = get_object_or_404(PlanAttendance.objects.select_related('plan'), pk=pk)
    if not is_plan_moderator(attendance.plan, request.user):
        messages.error(request, 'No puedes gestionar solicitudes de este plan.')
        return redirect('plan_detail', pk=attendance.plan_id)
    if status not in [PlanAttendance.Status.APPROVED, PlanAttendance.Status.DECLINED]:
        messages.error(request, 'Respuesta no válida.')
        return redirect('plan_detail', pk=attendance.plan_id)
    attendance.status = status
    attendance.save(update_fields=['status'])
    plan_url = reverse('plan_detail', kwargs={'pk': attendance.plan_id})
    if status == PlanAttendance.Status.APPROVED:
        sync_plan_conversation(attendance.plan)
        create_panel_notification(
            attendance.user,
            'Solicitud de plan aceptada',
            f'Te han aceptado en el plan {attendance.plan.title}.',
            plan_url,
        )
    else:
        create_panel_notification(
            attendance.user,
            'Solicitud de plan rechazada',
            f'Tu solicitud de plaza en {attendance.plan.title} ha sido rechazada.',
            plan_url,
        )
    notify_panel_users([request.user, attendance.user, *plan_moderator_users(attendance.plan)])
    messages.success(request, 'Solicitud de plan actualizada.')
    return redirect('plan_detail', pk=attendance.plan_id)

# Create your views here.
