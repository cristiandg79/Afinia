from django import forms

from .models import Publication


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file, initial) for file in data]
        return [single_file_clean(data, initial)] if data else []


class PublicationForm(forms.ModelForm):
    photos = MultipleImageField(
        label='Fotos',
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True, 'accept': 'image/*'}),
    )

    class Meta:
        model = Publication
        fields = ['link_url', 'message']
        labels = {
            'link_url': 'URL',
            'message': 'Mensaje',
        }
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Comparte algo con la comunidad...',
            }),
            'link_url': forms.URLInput(attrs={
                'placeholder': 'https://...',
            }),
        }
