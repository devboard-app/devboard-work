from typing import ClassVar

from rest_framework import serializers

from .models import Sprint


class SprintSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sprint
        fields: ClassVar = ['id', 'name', 'goal', 'start_date', 'end_date', 'status', 'project', 'created_by', 'created_at', 'updated_at']
        read_only_fields: ClassVar = ['id', 'created_by', 'created_at', 'updated_at', 'status']

class SprintListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sprint
        fields: ClassVar = ['id', 'name', 'status', 'start_date', 'end_date']

class SprintInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    goal = serializers.CharField(allow_blank=True, required=False, default='')
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('No fields to update.')
        return attrs

class SprintTicketInputSerializer(serializers.Serializer):
    ticket_id = serializers.UUIDField()