from django.contrib import admin

from .models import Group, GroupMembership, Plan, PlanAttendance


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'topic', 'privacy', 'created_by')
    search_fields = ('name', 'city', 'topic')
    list_filter = ('privacy', 'city')
    inlines = [GroupMembershipInline]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'starts_at', 'mood', 'capacity', 'created_by')
    search_fields = ('title', 'city', 'place')
    list_filter = ('mood', 'city')


admin.site.register(GroupMembership)
admin.site.register(PlanAttendance)

# Register your models here.
