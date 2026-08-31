import uuid
from typing import ClassVar

from django.contrib.postgres.fields import ArrayField
from django.db import models


class Comment(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    ticket = models.ForeignKey('tickets.Ticket', on_delete=models.CASCADE, related_name='comments')
    author_id = models.UUIDField()
    body = models.TextField()
    attachment_ids = ArrayField(models.UUIDField(), default=list, blank=True)
    mentioned_user_ids = ArrayField(models.UUIDField(), default=list, blank=True)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        ordering: ClassVar = ['created_at']
        indexes: ClassVar = [models.Index(fields=['ticket', 'created_at'])]

    def __str__(self):
        return str(self.id)