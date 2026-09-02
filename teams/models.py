import uuid
from typing import ClassVar

from django.db import models


class Team(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table= 'teams'
        ordering: ClassVar = ['name', 'id']

    def __str__(self):
        return self.name


class TeamMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user_id = models.UUIDField()
    role = models.CharField(max_length=10, choices=Role.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'memberships'
        ordering: ClassVar = ['joined_at', 'id']
        unique_together: ClassVar = [('user_id', 'team')]

    def __str__(self):
        return f'{self.user_id} - {self.team_id} ({self.role})' # type: ignore