from django.conf import settings
from django.db import models

from community.models import Group, Plan


class Publication(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publications')
    message = models.TextField(max_length=1200)
    link_url = models.URLField(blank=True)
    link_title = models.CharField(max_length=220, blank=True)
    link_description = models.TextField(blank=True)
    link_image_url = models.URLField(blank=True)
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
        return f'Foto de publicación {self.publication_id}'


class PublicationLike(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publication_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['publication', 'user'], name='unique_publication_like')
        ]

    def __str__(self):
        return f'{self.user} like {self.publication_id}'


class PublicationComment(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publication_comments')
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} comento {self.publication_id}'
