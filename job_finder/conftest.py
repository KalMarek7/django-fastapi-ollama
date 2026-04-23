import pytest
from rest_framework.test import APIClient

from accounts.models import CustomUser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    user = CustomUser.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client