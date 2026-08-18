import uuid
from typing import ClassVar

from django.db import models


class Label(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7) # #FF00FF
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='labels')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'labels'
        unique_together : ClassVar =[('project', 'name')]

    def __str__(self):
        return self.name
