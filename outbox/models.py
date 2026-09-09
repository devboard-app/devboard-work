import uuid
from typing import ClassVar

from django.db import models


class OutboxEvent(models.Model):
    class Channel(models.TextChoices):
        REDIS_STREAM = 'redis_stream', 'Redis Stream'
        EMAIL = 'email', 'Email'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    channel = models.CharField(max_length=32, choices=Channel.choices)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)

    class Meta:
        indexes: ClassVar = [models.Index(fields=['delivered_at', 'created_at'])]