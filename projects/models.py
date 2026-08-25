import uuid
from typing import ClassVar

from django.db import models


class Project(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='projects')
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table= 'projects'
        unique_together: ClassVar = [('team', 'key')]

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):

    class Role(models.TextChoices):
        LEAD = 'lead', 'Lead'
        CONTRIBUTOR = 'contributor', 'Contributor'
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user_id = models.UUIDField()
    role = models.CharField(max_length=11, choices=Role.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_memberships'
        unique_together: ClassVar = [('user_id', 'project')]

    def __str__(self):
        return f'{self.user_id} - {self.project.name} ({self.role})'