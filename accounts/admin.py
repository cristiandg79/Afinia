from django.contrib import admin

from .models import Connection, DatingAction, Profile, ProfilePhoto


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'onboarding_completed', 'updated_at')
    search_fields = ('user__username', 'city')
    list_filter = ('onboarding_completed', 'open_to_nearby', 'open_to_online')


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('requester', 'receiver', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ('profile', 'created_at')
    search_fields = ('profile__user__username',)


@admin.register(DatingAction)
class DatingActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'target', 'action', 'created_at')
    list_filter = ('action',)

# Register your models here.
