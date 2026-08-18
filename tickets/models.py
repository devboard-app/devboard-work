import uuid
from typing import ClassVar

from django.db import models


class Ticket(models.Model):
    class Type(models.TextChoices):
        EPIC = 'epic', 'Epic'
        BUG = 'bug', 'Bug'
        FEATURE = 'feature', 'Feature'
        TASK = 'task', 'Task'
        IMPROVEMENT = 'improvement', 'Improvement'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        BACKLOG = 'backlog', 'Backlog'
        TODO = 'todo', 'Todo'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        DONE = 'done', 'Done'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    ticket_number = models.PositiveIntegerField()
    key = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=11, choices=Type.choices)
    priority = models.CharField(max_length=8, choices=Priority.choices)
    status = models.CharField(max_length=11, choices=Status.choices)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tickets')
    assignee_id = models.UUIDField(null=True, blank=True)
    created_by = models.UUIDField()
    parent_epic = models.ForeignKey('self', null=True, blank=True, on_delete = models.SET_NULL, related_name='child_tickets')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    labels = models.ManyToManyField('labels.Label', blank=True, related_name='tickets')
    class Meta:
        db_table = 'tickets'
        unique_together : ClassVar = [('project', 'ticket_number')]

    def __str__(self):
        return self.key