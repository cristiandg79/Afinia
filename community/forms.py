from django import forms

from .models import Group, Plan


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'city', 'topic', 'privacy']
        labels = {
            'name': 'Nombre del grupo',
            'description': 'Descripción',
            'city': 'Ciudad',
            'topic': 'Tema',
            'privacy': 'Privacidad',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class PlanForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        label='Fecha y hora',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )

    class Meta:
        model = Plan
        fields = ['title', 'description', 'city', 'place', 'starts_at', 'capacity', 'mood', 'accessibility_info']
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'city': 'Ciudad',
            'place': 'Lugar',
            'starts_at': 'Fecha y hora',
            'capacity': 'Plazas',
            'mood': 'Ambiente',
            'accessibility_info': 'Información de accesibilidad',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'accessibility_info': forms.Textarea(attrs={'rows': 3}),
        }
