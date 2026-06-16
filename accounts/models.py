from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .locations import LOCATION_COUNTRY_CHOICES, LOCATION_COUNTRY_LABELS


class Profile(models.Model):
    class Goal(models.TextChoices):
        FRIENDSHIP = 'friendship', 'Amistad'
        DATING = 'dating', 'Citas'
        GROUPS = 'groups', 'Grupos y planes'
        TALK = 'talk', 'Hablar online'

    class Visibility(models.TextChoices):
        PRIVATE = 'private', 'Solo yo'
        CONNECTIONS = 'connections', 'Conexiones'
        PUBLIC = 'public', 'Visible en mi perfil'

    class Sex(models.TextChoices):
        WOMAN = 'woman', 'Mujer'
        MAN = 'man', 'Hombre'
        NON_BINARY = 'non_binary', 'No binario'
        OTHER = 'other', 'Otro'
        PREFER_NOT_SAY = 'prefer_not_say', 'Prefiero no decirlo'

    class Orientation(models.TextChoices):
        HETEROSEXUAL = 'heterosexual', 'Heterosexual'
        HOMOSEXUAL = 'homosexual', 'Homosexual'
        BISEXUAL = 'bisexual', 'Bisexual'
        PANSEXUAL = 'pansexual', 'Pansexual'
        ASEXUAL = 'asexual', 'Asexual'
        QUESTIONING = 'questioning', 'En duda'
        OTHER = 'other', 'Otra'
        PREFER_NOT_SAY = 'prefer_not_say', 'Prefiero no decirlo'

    class Smoker(models.TextChoices):
        NO = 'no', 'No'
        SOMETIMES = 'sometimes', 'A veces'
        YES = 'yes', 'Si'
        PREFER_NOT_SAY = 'prefer_not_say', 'Prefiero no decirlo'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=80)
    country = models.CharField(max_length=8, choices=LOCATION_COUNTRY_CHOICES, default='ES')
    city = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    goals = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    social_preferences = models.JSONField(default=list, blank=True)
    dating_preferences = models.JSONField(default=dict, blank=True)
    health_context = models.JSONField(default=list, blank=True)
    sex = models.CharField(max_length=24, choices=Sex.choices, blank=True)
    orientation = models.CharField(max_length=24, choices=Orientation.choices, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    height_cm = models.PositiveSmallIntegerField(blank=True, null=True)
    weight_kg = models.PositiveSmallIntegerField(blank=True, null=True)
    smoker = models.CharField(max_length=24, choices=Smoker.choices, blank=True)
    accessibility_notes = models.TextField(blank=True)
    accessibility_visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    open_to_nearby = models.BooleanField(default=True)
    open_to_online = models.BooleanField(default=True)
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'username': self.user.username})

    @property
    def country_label(self):
        return LOCATION_COUNTRY_LABELS.get(self.country, self.country or '')

    @property
    def location_label(self):
        if self.city and self.country_label:
            return f'{self.city}, {self.country_label}'
        return self.city or self.country_label or 'Online'

    def goal_labels(self):
        labels = dict(self.Goal.choices)
        return [labels.get(goal, goal) for goal in self.goals]

    def interest_labels(self):
        labels = {
            'cafe': 'Café y charla',
            'cinema': 'Cine y series',
            'gaming': 'Videojuegos',
            'reading': 'Lectura',
            'music': 'Música',
            'walks': 'Paseos tranquilos',
            'art': 'Arte',
            'sports': 'Actividad física adaptada',
            'pets': 'Animales',
            'support': 'Apoyo entre iguales',
        }
        return [labels.get(interest, interest) for interest in self.interests]

    def social_preference_labels(self):
        labels = {
            'chat_first': 'Prefiero hablar por chat antes de quedar',
            'small_groups': 'Me siento mejor en grupos pequeños',
            'quiet_places': 'Prefiero lugares tranquilos',
            'clear_plans': 'Me ayuda saber el plan con antelacion',
            'slow_pace': 'Me gusta ir poco a poco',
        }
        return [labels.get(preference, preference) for preference in self.social_preferences]

    def health_context_labels(self):
        labels = {
            'physical_disability': 'Discapacidad física o movilidad reducida',
            'visual_disability': 'Discapacidad visual',
            'hearing_disability': 'Discapacidad auditiva',
            'intellectual_disability': 'Discapacidad intelectual',
            'autism': 'Autismo / espectro autista',
            'adhd': 'TDAH',
            'anxiety': 'Ansiedad',
            'depression': 'Depresion',
            'bipolar': 'Trastorno bipolar',
            'ocd': 'TOC',
            'ptsd': 'Trauma / TEPT',
            'psychosis': 'Psicosis o esquizofrenia',
            'eating_disorder': 'Trastorno de la conducta alimentaria',
            'chronic_illness': 'Enfermedad crónica',
            'rare_disease': 'Enfermedad rara',
            'brain_injury': 'Daño cerebral adquirido',
            'pain_fatigue': 'Dolor cronico o fatiga',
            'other': 'Otra situación',
            'prefer_not_detail': 'Prefiero no detallarlo',
        }
        return [labels.get(item, item) for item in self.health_context]

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        years = today.year - self.birth_date.year
        before_birthday = (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        return years - int(before_birthday)

    @property
    def horoscope_sign(self):
        if not self.birth_date:
            return ''
        month = self.birth_date.month
        day = self.birth_date.day
        signs = [
            ((1, 20), 'Capricornio'), ((2, 19), 'Acuario'), ((3, 21), 'Piscis'),
            ((4, 20), 'Aries'), ((5, 21), 'Tauro'), ((6, 21), 'Geminis'),
            ((7, 23), 'Cancer'), ((8, 23), 'Leo'), ((9, 23), 'Virgo'),
            ((10, 23), 'Libra'), ((11, 22), 'Escorpio'), ((12, 22), 'Sagitario'),
            ((12, 32), 'Capricornio'),
        ]
        for (sign_month, sign_day), sign in signs:
            if (month, day) < (sign_month, sign_day):
                return sign
        return 'Capricornio'


class ProfilePhoto(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='extra_photos')
    image = models.ImageField(upload_to='profiles/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Foto de {self.profile.user.username}'


class DatingAction(models.Model):
    class Action(models.TextChoices):
        LIKE = 'like', 'Me interesa'
        PASS = 'pass', 'Pasar'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dating_actions')
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dating_received_actions')
    action = models.CharField(max_length=10, choices=Action.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'target'], name='unique_dating_action')
        ]

    def __str__(self):
        return f'{self.user} -> {self.target} ({self.action})'


class Connection(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        ACCEPTED = 'accepted', 'Aceptada'
        DECLINED = 'declined', 'Rechazada'
        BLOCKED = 'blocked', 'Bloqueada'

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['requester', 'receiver'], name='unique_connection_request')
        ]

    def __str__(self):
        return f'{self.requester} -> {self.receiver} ({self.status})'

# Create your models here.
