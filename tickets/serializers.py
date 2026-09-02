from typing import ClassVar

from rest_framework import serializers

from labels.serializers import LabelListSerializer

from .models import STORY_POINTS, Ticket


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

class TicketInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    type = serializers.ChoiceField(choices=Ticket.Type.choices)
    description = serializers.CharField(allow_blank=True, required=False, default='')
    priority = serializers.ChoiceField(choices=Ticket.Priority.choices, required=False, default=Ticket.Priority.MEDIUM)
    status = serializers.ChoiceField(choices=Ticket.Status.choices, required=False, default=Ticket.Status.BACKLOG)
    assignee_id = serializers.UUIDField(required=False, allow_null=True)
    parent_epic = serializers.UUIDField(required=False, allow_null=True)
    story_points = serializers.ChoiceField(choices=STORY_POINTS, required=False, allow_null=True, error_messages={'invalid_choice': 'Story point must be a Fibonacci number: 1, 2, 3, 5, 8, 13, 21.'})
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('No fields to update.')
        return attrs