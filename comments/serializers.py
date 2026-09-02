from typing import ClassVar

from rest_framework import serializers

from .models import MAX_ATTACHMENTS, Comment


class CommentSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields: ClassVar = [
            'id', 'ticket', 'author_id', 'body', 'attachment_ids', 'attachments',
            'mentioned_user_ids', 'is_edited', 'created_at', 'updated_at' 
        ]
        read_only_fields: ClassVar =[
            'id', 'ticket', 'author_id', 'mentioned_user_ids', 'is_edited', 'created_at', 'updated_at',
        ]

    def get_attachments(self, obj) -> list[dict]:
        resolved = self.context.get('resolved_attachments', {})
        return [resolved[str(i)] for i in obj.attachment_ids if str(i) in resolved]

class CommentInputSerializer(serializers.Serializer):
    body = serializers.CharField(trim_whitespace=True, allow_blank=False)
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=MAX_ATTACHMENTS,
        required=False, default=list,
    )