from django.contrib import admin

from .models import Publication, PublicationPhoto


class PublicationPhotoInline(admin.TabularInline):
    model = PublicationPhoto
    extra = 0


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at', 'link_url')
    search_fields = ('author__username', 'message', 'link_url')
    inlines = [PublicationPhotoInline]
