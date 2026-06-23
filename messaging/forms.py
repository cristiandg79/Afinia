from django import forms

from .models import MESSAGE_MAX_LENGTH, Message


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body', 'image']
        labels = {
            'body': 'Mensaje',
            'image': 'Imagen',
        }
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': MESSAGE_MAX_LENGTH,
                'placeholder': 'Escribe con calma. No hace falta hacerlo perfecto.',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].required = False
        self.fields['image'].required = False

    def clean(self):
        cleaned_data = super().clean()
        body = (cleaned_data.get('body') or '').strip()
        image = cleaned_data.get('image')
        if len(body) > MESSAGE_MAX_LENGTH:
            self.add_error('body', f'El mensaje no puede superar {MESSAGE_MAX_LENGTH} caracteres.')
        if not body and not image:
            raise forms.ValidationError('Escribe un mensaje o añade una imagen.')
        cleaned_data['body'] = body
        return cleaned_data
