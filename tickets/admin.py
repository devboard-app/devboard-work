from typing import ClassVar

from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display: ClassVar = ['key', 'title', 'type', 'priority', 'status', 'project', 'assignee_id', 'created_by']
    list_filter: ClassVar = ['type', 'priority', 'status']
    search_fields: ClassVar = ['key', 'title']
    