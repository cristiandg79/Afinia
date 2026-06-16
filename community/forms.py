from django import forms

from accounts.locations import LOCATION_COUNTRY_CHOICES

from .models import Group, Plan


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'country', 'city', 'topic', 'privacy']
        labels = {
            'name': 'Nombre del grupo',
            'description': 'Descripción',
            'country': 'País',
            'city': 'Ciudad',
            'topic': 'Tema',
            'privacy': 'Privacidad',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'country': forms.Select(attrs={'data-location-country': 'true'}),
            'city': forms.TextInput(attrs={
                'placeholder': 'Ej. Madrid',
                'autocomplete': 'address-level2',
                'data-location-city': 'true',
                'list': 'location-city-suggestions',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = LOCATION_COUNTRY_CHOICES


class PlanForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        label='Fecha y hora',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = Plan
        fields = ['title', 'description', 'country', 'city', 'place', 'starts_at', 'capacity', 'mood', 'accessibility_info']
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'country': 'País',
            'city': 'Ciudad',
            'place': 'Lugar',
            'starts_at': 'Fecha y hora',
            'capacity': 'Plazas',
            'mood': 'Ambiente',
            'accessibility_info': 'Accesibilidad y comodidad',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'country': forms.Select(attrs={'data-location-country': 'true'}),
            'city': forms.TextInput(attrs={
                'placeholder': 'Ej. Barcelona',
                'autocomplete': 'address-level2',
                'data-location-city': 'true',
                'list': 'location-city-suggestions',
            }),
            'accessibility_info': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ej. entrada sin escaleras, poco ruido, baño adaptado, transporte cercano...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = LOCATION_COUNTRY_CHOICES
        self.fields['accessibility_info'].help_text = (
            'Ej. entrada sin escaleras, poco ruido, baño adaptado, transporte cercano, '
            'posibilidad de sentarse o cualquier detalle útil.'
        )
