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
        