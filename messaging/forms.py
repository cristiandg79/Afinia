from django import forms

from .models import Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'image']
        labels = {
            'body': 'Mensaje',
            'image': 'Imagen',
        }
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe con calma. No hace falta hacerlo perfecto.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].required = False
        self.fields['image'].required = False

    def clean(self):
        cleaned_data = super().clean()
        body = (cleaned_data.get('body') or '').strip()
        image = cleaned_data.get('image')
        if not body and not image:
            raise forms.ValidationError('Escribe un mensaje o añade una imagen.')
        cleaned_data['body'] = body
        return cleaned_data
