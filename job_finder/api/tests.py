import uuid

import pytest
from home.models import JobListing, Portal, SystemInstruction
from rest_framework import status
from tasks.models import Task


@pytest.mark.django_db
class TestJobListingSerializer:
    def test_job_listing_serializer_fields(self):
        from api.serializers import JobListingSerializer

        portal = Portal.objects.create(name="TestPortal", url="https://test.com")
        job = JobListing.objects.create(
            title="Python Dev",
            company="TechCorp",
            text_content="Job description",
            url="https://test.com/job/1",
            portal=portal,
        )
        serializer = JobListingSerializer(job)
        data = serializer.data
        assert data["title"] == "Python Dev"
        assert data["company"] == "TechCorp"
        assert data["portal"] == portal.id


@pytest.mark.django_db
class TestTaskSerializer:
    def test_task_serializer_fields(self):
        from api.serializers import TaskSerializer

        task = Task.objects.create(status="pending")
        serializer = TaskSerializer(task)
        data = serializer.data
        assert "task_id" in data
        assert data["status"] == "pending"


@pytest.mark.django_db
class TestPortalSerializer:
    def test_portal_serializer_fields(self):
        from api.serializers import PortalSerializer

        portal = Portal.objects.create(name="JustJoinIT", url="https://justjoin.it")
        serializer = PortalSerializer(portal)
        data = serializer.data
        assert data["name"] == "JustJoinIT"
        assert data["url"] == "https://justjoin.it"


@pytest.mark.django_db
class TestSystemInstructionSerializer:
    def test_system_instruction_serializer_fields(self):
        from api.serializers import SystemInstructionSerializer

        instruction = SystemInstruction.objects.create(
            name="Extract", instruction="Extract job details"
        )
        serializer = SystemInstructionSerializer(instruction)
        data = serializer.data
        assert data["name"] == "Extract"
        assert data["instruction"] == "Extract job details"


@pytest.mark.django_db
class TestTaskListAPI:
    def test_task_list_requires_auth(self, api_client):
        response = api_client.get("/api/tasks/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_task_list_returns_empty_initially(self, authenticated_client):
        response = authenticated_client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []

    def test_task_list_returns_tasks(self, authenticated_client):
        Task.objects.create(status="completed")
        response = authenticated_client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestTaskCreateAPI:
    def test_task_create_returns_201(self, authenticated_client):
        task_id = str(uuid.uuid4())
        response = authenticated_client.post(
            "/api/tasks/", {"task_id": task_id, "status": "pending"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.filter(task_id=task_id).exists()

    def test_task_update_returns_200(self, authenticated_client):
        task_id = str(uuid.uuid4())
        authenticated_client.post(
            "/api/tasks/", {"task_id": task_id, "status": "pending"}
        )
        response = authenticated_client.post(
            "/api/tasks/", {"task_id": task_id, "status": "completed"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert Task.objects.get(task_id=task_id).status == "completed"


@pytest.mark.django_db
class TestTaskDetailAPI:
    def setup_method(self):
        self.task = Task.objects.create(status="pending")

    def test_task_detail_get(self, authenticated_client):
        response = authenticated_client.get(f"/api/tasks/{self.task.task_id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "pending"

    def test_task_detail_update(self, authenticated_client):
        response = authenticated_client.patch(
            f"/api/tasks/{self.task.task_id}/", {"status": "completed"}
        )
        assert response.status_code == status.HTTP_200_OK
        self.task.refresh_from_db()
        assert self.task.status == "completed"

    def test_task_detail_delete(self, authenticated_client):
        response = authenticated_client.delete(f"/api/tasks/{self.task.task_id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(task_id=self.task.task_id).exists()


@pytest.mark.django_db
class TestJobListingListAPI:
    def setup_method(self):
        self.portal = Portal.objects.create(name="TestPortal", url="https://test.com")

    def test_job_listing_list_requires_auth(self, api_client):
        response = api_client.get("/api/job_listings/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_job_listing_list_returns_empty(self, authenticated_client):
        response = authenticated_client.get("/api/job_listings/")
        assert response.status_code == status.HTTP_200_OK

    def test_job_listing_list_filter_by_portal(self, authenticated_client):
        JobListing.objects.create(
            title="Job 1",
            text_content="content",
            url="https://test.com/1",
            portal=self.portal,
        )
        response = authenticated_client.get(
            f"/api/job_listings/?portal={self.portal.id}"
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestJobListingCreateAPI:
    def setup_method(self):
        self.portal = Portal.objects.create(name="TestPortal", url="https://test.com")

    def test_job_listing_create_returns_201(self, authenticated_client):
        response = authenticated_client.post(
            "/api/job_listings/",
            {
                "title": "Python Dev",
                "company": "TechCorp",
                "text_content": "Description",
                "url": "https://test.com/job/new",
                "portal": self.portal.id,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert JobListing.objects.filter(title="Python Dev").exists()

    def test_job_listing_update_returns_200(self, authenticated_client):
        url = "https://test.com/job/unique"
        authenticated_client.post(
            "/api/job_listings/",
            {
                "title": "First",
                "text_content": "desc",
                "url": url,
                "portal": self.portal.id,
            },
        )
        response = authenticated_client.post(
            "/api/job_listings/",
            {
                "title": "Updated",
                "text_content": "desc",
                "url": url,
                "portal": self.portal.id,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert JobListing.objects.filter(url=url, title="Updated").exists()


@pytest.mark.django_db
class TestPortalListAPI:
    def test_portal_list_returns_empty(self, authenticated_client):
        response = authenticated_client.get("/api/portals/")
        assert response.status_code == status.HTTP_200_OK

    def test_portal_create(self, authenticated_client):
        response = authenticated_client.post(
            "/api/portals/", {"name": "NewPortal", "url": "https://newportal.com"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Portal.objects.filter(name="NewPortal").exists()


@pytest.mark.django_db
class TestSystemInstructionListAPI:
    def test_system_instruction_list(self, authenticated_client):
        SystemInstruction.objects.create(name="Test", instruction="Do something")
        response = authenticated_client.get("/api/system_instructions/")
        assert response.status_code == status.HTTP_200_OK

    def test_system_instruction_create(self, authenticated_client):
        response = authenticated_client.post(
            "/api/system_instructions/",
            {"name": "Extract Job", "instruction": "Extract details"},
        )
        assert response.status_code == status.HTTP_201_CREATED
