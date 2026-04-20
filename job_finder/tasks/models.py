import uuid

from django.db import models

# Create your models here.
TASK_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("failed", "Failed"),
    ("completed_with_errors", "Completed with Errors"),
)


class Task(models.Model):
    task_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    status = models.CharField(
        max_length=50, choices=TASK_STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_id} - {self.status}"
