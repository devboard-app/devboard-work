from typing import ClassVar

from rest_framework import serializers

from .models import Team, TeamMembership


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields: ClassVar = ['id', 'name', 'description', 'owner_id', 'created_at']
        read_only_fields: ClassVar = ['id', 'owner_id', 'created_at']

class TeamMembershipSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamMembership
        fields: ClassVar = ['id', 'team', 'user_id', 'role', 'joined_at']
        read_only_fields: ClassVar = ['id', 'team', 'user_id', 'joined_at']