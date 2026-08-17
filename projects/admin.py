from typing import ClassVar

from django.contrib import admin

from .models import Project, ProjectMembership


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['name', 'key', 'created_by', 'created_at']
    search_fields: ClassVar = ['name', 'key']

@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['project', 'user_id', 'role', 'joined_at']
    list_filter: ClassVar = ['role']
    search_fields: ClassVar = ['project__name']