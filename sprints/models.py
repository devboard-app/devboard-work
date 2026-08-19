import uuid

from django.db import models


class Sprint(models.Model):

    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    goal = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='sprints')
    created_by = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name