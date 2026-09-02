from typing import ClassVar

from rest_framework import serializers

from .models import DEFAULT_COLOR, Label


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields: ClassVar = ['id', 'name', 'color', 'project', 'created_at']
        read_only_fields: ClassVar = ['id', 'project', 'created_at']

class LabelListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields: ClassVar = ['id', 'name', 'color']

class LabelInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    color = serializers.RegexField(
        r'^#[0-9A-Fa-f]{6}$',
        required=False, default=DEFAULT_COLOR,
        error_messages={'invalid': 'Color must be a hex code like #FF00FF.'},
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('No fields to update.')
        return attrs

class TicketLabelInputSerializer(serializers.Serializer):
    label_id = serializers.UUIDField()