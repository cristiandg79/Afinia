from django.conf import settings
from django.db import models
from django.urls import reverse

from accounts.locations import LOCATION_COUNTRY_CHOICES, LOCATION_COUNTRY_LABELS


class Group(models.Model):
    class Privacy(models.TextChoices):
        OPEN = 'open', 'Abierto'
        REQUEST = 'request', 'Con solicitud'
        PRIVATE = 'private', 'Privado'

    name = models.CharField(max_length=120)
    description = models.TextField()
    country = models.CharField(max_length=8, choices=LOCATION_COUNTRY_CHOICES, default='ES')
    city = models.CharField(max_length=120, blank=True)
    topic = models.CharField(max_length=120, blank=True)
    privacy = models.CharField(max_length=20, choices=Privacy.choices, default=Privacy.REQUEST)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='GroupMembership', related_name='community_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('group_detail', kwargs={'pk': self.pk})

    @property
    def country_label(self):
        return LOCATION_COUNTRY_LABELS.get(self.country, self.country or '')

    @property
    def location_label(self):
        if self.city and self.country_label:
            return f'{self.city}, {self.country_label}'
        return self.city or self.country_label or 'Online'


class GroupMembership(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobada'
        DECLINED = 'declined', 'Rechazada'
        MODERATOR = 'moderator', 'Moderador'

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'user'], name='unique_group_membership')
        ]

    def __str__(self):
        return f'{self.user} en {self.group}'


class Plan(models.Model):
    class Mood(models.TextChoices):
        CALM = 'calm', 'Tranquilo'
        SOCIAL = 'social', 'Social'
        OUTDOOR = 'outdoor', 'Exterior'
        ONLINE = 'online', 'Online'

    title = models.CharField(max_length=140)
    description = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='plans')
    country = models.CharField(max_length=8, choices=LOCATION_COUNTRY_CHOICES, default='ES')
    city = models.CharField(max_length=120, blank=True)
    place = models.CharField(max_length=180, blank=True)
    starts_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=8)
    mood = models.CharField(max_length=20, choices=Mood.choices, default=Mood.CALM)
    accessibility_info = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_plans')
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, through='PlanAttendance', related_name='plans')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return self.title

    @property
    def country_label(self):
        return LOCATION_COUNTRY_LABELS.get(self.country, self.country or '')

    @property
    def location_label(self):
        if self.city and self.country_label:
            return f'{self.city}, {self.country_label}'
        return self.city or self.country_label or 'Online'


class PlanAttendance(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'requested', 'Solicitado'
        APPROVED = 'approved', 'Miembro'
        MODERATOR = 'moderator', 'Moderador'
        DECLINED = 'declined', 'Rechazado'

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['plan', 'user'], name='unique_plan_attendance')
        ]

# Create your models here.
