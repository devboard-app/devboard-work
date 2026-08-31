from typing import ClassVar

from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields: ClassVar = [
            'id', 'ticket', 'author_id', 'body', 'attachment_ids',
            'mentioned_user_ids', 'is_edited', 'created_at', 'updated_at' 
        ]
        read_only_fields: ClassVar =[
            'id', 'ticket', 'author_id', 'is_edited', 'created_at', 'updated_at',
        ]