from typing import ClassVar

from django.contrib import admin

from .models import Label


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['name', 'color', 'project', 'created_at']
    list_filter: ClassVar = ['project']
    search_fields: ClassVar = ['name']