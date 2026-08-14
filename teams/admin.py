from typing import ClassVar

from django.contrib import admin

from .models import Team, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['name', 'owner_id', 'created_at']
    search_fields: ClassVar = ['name']

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['team', 'user_id', 'role', 'joined_at']
    list_filter: ClassVar = ['role']
    search_fields: ClassVar = ['team__name']
    