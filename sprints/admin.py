from typing import ClassVar

from django.contrib import admin

from .models import Sprint


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display: ClassVar= ['name', 'project', 'status', 'start_date', 'end_date', 'created_at']
    list_filter: ClassVar = ['status', 'project']

