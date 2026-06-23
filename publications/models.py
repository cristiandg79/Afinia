from django.conf import settings
from django.db import models

from community.models import Group, Plan


class Publication(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publications')
    message = models.TextField(max_length=1200)
    link_url = models.URLField(blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='publications')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name='publications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author} - {self.created_at:%Y-%m-%d}'


class PublicationPhoto(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='publications/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Foto de publicacion {self.publication_id}'
