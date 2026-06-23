from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .choices import HEALTH_CONTEXT_CHOICES
from .locations import LOCATION_COUNTRY_CHOICES
from .models import Profile


GOAL_CHOICES = [
    ('friendship', 'Amistad'),
    ('dating', 'Citas'),
    ('groups', 'Grupos y planes'),
    ('talk', 'Hablar online'),
]

INTEREST_CHOICES = [
    ('cafe', 'Café y charla'),
    ('cinema', 'Cine y series'),
    ('gaming', 'Videojuegos'),
    ('reading', 'Lectura'),
    ('music', 'Música'),
    ('walks', 'Paseos tranquilos'),
    ('art', 'Arte'),
    ('sports', 'Actividad física'),
    ('pets', 'Animales'),
    ('support', 'Apoyo entre iguales'),
]

SOCIAL_CHOICES = [
    ('chat_first', 'Prefiero hablar por chat antes de quedar'),
    ('small_groups', 'Me siento mejor en grupos pequeños'),
    ('quiet_places', 'Prefiero lugares tranquilos'),
    ('clear_plans', 'Me ayuda saber el plan con antelacion'),
    ('slow_pace', 'Me gusta ir poco a poco'),
]

PHOTO_REQUIRED_MESSAGE = 'Es obligatorio poner una foto principal. Puede ser una foto, avatar, logo o paisaje.'


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com'}))
    email2 = forms.EmailField(label='Repite el email', widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com'}))
    accept_terms = forms.BooleanField(
        label='Acepto los términos y la política de privacidad',
        required=True,
        error_messages={'required': 'Debes aceptar los Términos y Condiciones y la Política de Privacidad para crear la cuenta.'},
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'email2', 'password1', 'password2', 'accept_terms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['username'].help_text = 'Este será tu nick público. No puede estar repetido.'
        self.fields['username'].widget.attrs.update({'placeholder': 'ej. alex_madrid'})
        self.password_help_text = self.fields['password1'].help_text
        self.fields['password1'].help_text = ''
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Repite la contraseña'

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este email.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email2 = cleaned_data.get('email2')
        if email and email2 and email.lower() != email2.lower():
            self.add_error('email2', 'Los emails no coinciden.')
        return cleaned_data


class ProfileForm(forms.ModelForm):
    extra_photo_1 = forms.ImageField(label='Foto adicional 1', required=False)
    extra_photo_2 = forms.ImageField(label='Foto adicional 2', required=False)
    extra_photo_3 = forms.ImageField(label='Foto adicional 3', required=False)
    extra_photo_4 = forms.ImageField(label='Foto adicional 4', required=False)
    goals = forms.MultipleChoiceField(
        label='Qué buscas',
        choices=GOAL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    interests = forms.MultipleChoiceField(
        label='Intereses',
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    social_preferences = forms.MultipleChoiceField(
        label='Preferencias para relacionarte',
        choices=SOCIAL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    health_context = forms.MultipleChoiceField(
        label='Situación personal',
        choices=HEALTH_CONTEXT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Profile
        fields = [
            'photo',
            'country',
            'city',
            'bio',
            'goals',
            'interests',
            'social_preferences',
            'health_context',
            'sex',
            'orientation',
            'birth_date',
            'height_cm',
            'weight_kg',
        ]
        widgets = {
            'photo': forms.FileInput(attrs={'accept': 'image/*'}),
            'country': forms.Select(attrs={'data-location-country': 'true'}),
            'city': forms.TextInput(attrs={
                'placeholder': 'Ej. Madrid',
                'autocomplete': 'address-level2',
                'data-location-city': 'true',
                'list': 'location-city-suggestions',
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Cuenta algo sencillo: que te gusta, que buscas o que plan te apetece.',
            }),
            'birth_date': forms.DateInput(
                attrs={'type': 'date', 'data-birth-date': 'true'},
                format='%Y-%m-%d',
            ),
            'height_cm': forms.NumberInput(attrs={'min': 100, 'max': 230, 'placeholder': 'Ej. 170'}),
            'weight_kg': forms.NumberInput(attrs={'min': 30, 'max': 250, 'placeholder': 'Ej. 70'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].label = 'Foto principal'
        self.fields['photo'].help_text = 'Obligatoria. Puede ser una foto, avatar, logo o paisaje.'
        self.fields['photo'].required = False
        self.fields['country'].label = 'País'
        self.fields['country'].choices = LOCATION_COUNTRY_CHOICES
        self.fields['city'].label = 'Ciudad'
        self.fields['bio'].label = 'Presentación breve'
        self.fields['health_context'].label = 'Discapacidad, neurodivergencia o salud mental'
        self.fields['sex'].label = 'Sexo'
        self.fields['orientation'].label = 'Orientación sexual'
        self.fields['birth_date'].label = 'Fecha de nacimiento'
        self.fields['height_cm'].label = 'Altura (cm)'
        self.fields['weight_kg'].label = 'Peso (kg)'
        optional_selects = ['sex', 'orientation']
        for field_name in optional_selects:
            self.fields[field_name].required = False
            choices = [(value, label) for value, label in self.fields[field_name].choices if value]
            self.fields[field_name].choices = [('', 'Prefiero no responder ahora')] + choices

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if not birth_date:
            return birth_date
        today = timezone.localdate()
        if birth_date > today:
            raise forms.ValidationError('La fecha de nacimiento no puede ser futura.')
        age = today.year - birth_date.year - int((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise forms.ValidationError('Debes tener al menos 18 años para crear un perfil.')
        return birth_date

    def clean(self):
        cleaned_data = super().clean()
        photo = cleaned_data.get('photo')
        has_current_photo = bool(self.instance and self.instance.photo)
        has_uploaded_photo = bool(self.files.get(self.add_prefix('photo')))
        photo_was_cleared = photo is False
        keeps_current_photo = has_current_photo and not photo_was_cleared

        if not has_uploaded_photo and not keeps_current_photo:
            self.add_error('photo', PHOTO_REQUIRED_MESSAGE)

        return cleaned_data
