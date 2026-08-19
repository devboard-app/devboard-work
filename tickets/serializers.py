from typing import ClassVar

from rest_framework import serializers

from labels.serializers import LabelListSerializer

from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    labels = LabelListSerializer(many=True, read_only=True)
    class Meta:
        model = Ticket
        fields: ClassVar =['id', 'key', 'ticket_number', 'title', 'description', 'type', 'priority', 'status', 'project', 'assignee_id', 'created_by', 'parent_epic', 'due_date', 'created_at', 'updated_at', 'labels', 'story_points']
        read_only_fields: ClassVar = ['id', 'key', 'ticket_number', 'created_by', 'created_at', 'updated_at', 'labels']

class TicketListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Ticket
        fields: ClassVar =['id', 'key', 'title', 'type', 'priority', 'status', 'story_points', 'assignee_id', 'due_date']