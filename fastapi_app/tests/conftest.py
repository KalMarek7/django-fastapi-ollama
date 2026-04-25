from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def create_mock_drf_client():
    """Factory for mock DRF client."""
    client = MagicMock()
    client.get.return_value = [
        {
            "task_id": "test-uuid-123",
            "status": "pending",
            "created_at": "2026-04-24T10:00:00Z",
        }
    ]
    client.post.return_value = {"task_id": "test-uuid-123", "status": "pending"}
    client.close = MagicMock()
    return client


@pytest.fixture
def mock_drf_client():
    """Mock DRF client for synchronous tests."""
    return create_mock_drf_client()


@pytest.fixture
def mock_async_drf_client():
    """Mock Async DRF client for async tests."""
    client = AsyncMock()
    client.get.return_value = [
        {
            "task_id": "test-uuid-123",
            "status": "pending",
            "created_at": "2026-04-24T10:00:00Z",
        }
    ]
    client.post.return_value = {"task_id": "test-uuid-123", "status": "pending"}
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_llm():
    """Mock LLM client for tests."""
    mock_instance = MagicMock()
    mock_instance.get_listings_details.return_value = MagicMock(
        model_dump=MagicMock(
            return_value={
                "title": "Python Developer",
                "company": "TechCorp",
                "years_of_experience": 3,
                "salary": "200000-300000 PLN",
            }
        )
    )
    return mock_instance


@pytest.fixture
def test_client(mock_async_drf_client):
    """FastAPI TestClient with mocked dependencies."""
    with patch("main.AsyncDRFClient", return_value=mock_async_drf_client):
        with patch("main.DRFClient", side_effect=create_mock_drf_client):
            with patch(
                "main.perform_scraping_task"
            ):  # Prevent background task from running
                from main import app

                yield TestClient(app)
