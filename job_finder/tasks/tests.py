import pytest
from .models import Task


@pytest.mark.django_db
class TestTaskModel:
    def test_task_creation_default_status(self):
        task = Task.objects.create()
        assert task.task_id is not None
        assert task.status == "pending"

    def test_task_creation_with_status(self):
        task = Task.objects.create(status="in_progress")
        assert task.status == "in_progress"

    def test_task_uuid_is_unique(self):
        task1 = Task.objects.create()
        task2 = Task.objects.create()
        assert task1.task_id != task2.task_id

    def test_task_str_representation(self):
        task = Task.objects.create(status="completed")
        assert str(task) == f"{task.task_id} - completed"

    def test_task_status_choices(self):
        valid_statuses = [
            "pending",
            "in_progress",
            "completed",
            "failed",
            "completed_with_errors",
        ]
        for status in valid_statuses:
            task = Task.objects.create(status=status)
            assert task.status == status

    def test_task_timestamps_auto(self):
        task = Task.objects.create()
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_update_updates_timestamp(self):
        task = Task.objects.create()
        original_updated = task.updated_at
        task.status = "completed"
        task.save()
        assert task.updated_at > original_updated