from typing import ClassVar

from rest_framework import serializers

from .models import Project, ProjectMembership


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields: ClassVar = ['id', 'name', 'key', 'description', 'team', 'created_by', 'created_at']
        read_only_fields: ClassVar = ['id', 'created_by', 'created_at']

class ProjectMembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectMembership
        fields: ClassVar = ['id', 'project', 'user_id', 'role', 'joined_at']
        read_only_fields: ClassVar = ['id', 'project', 'user_id', 'joined_at']