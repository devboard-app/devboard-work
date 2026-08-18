from typing import ClassVar

from rest_framework import serializers

from .models import Label


class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields: ClassVar = ['id', 'name', 'color', 'project', 'created_at']
        read_only_fields: ClassVar = ['id', 'project', 'created_at']

class LabelListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields: ClassVar = ['id', 'name', 'color']