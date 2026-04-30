class TestGetTaskStatus:
    def test_get_task_status_success(self, test_client, mock_async_drf_client):
        task_id = "550e8400-e29b-41d4-a716-446655440000"
        response = test_client.get(f"/tasks/status/{task_id}")
        assert response.status_code == 200

    def test_get_task_status_returns_list(self, test_client, mock_async_drf_client):
        task_id = "550e8400-e29b-41d4-a716-446655440000"
        response = test_client.get(f"/tasks/status/{task_id}")
        assert isinstance(response.json(), list)


class TestScheduleScrapingTask:
    def test_schedule_empty_payload(self, test_client, mock_async_drf_client):
        response = test_client.post("/tasks/schedule-scraping", json={})
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status_url" in data
        assert data["message"] == "Task started in background"

    def test_schedule_empty_payload_no_brackets(
        self, test_client, mock_async_drf_client
    ):
        response = test_client.post("/tasks/schedule-scraping")
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_schedule_specific_url_and_portal(self, test_client, mock_async_drf_client):
        response = test_client.post(
            "/tasks/schedule-scraping",
            json={
                "url": "https://justjoin.it/api/candidate-api/offers/python-dev",
                "portal": "JustJoinIT",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data

    def test_schedule_only_url_invalid(self, test_client, mock_async_drf_client):
        response = test_client.post(
            "/tasks/schedule-scraping",
            json={"url": "https://justjoin.it/job/python-dev"},
        )
        assert response.status_code == 422

    def test_schedule_only_portal_invalid(self, test_client, mock_async_drf_client):
        response = test_client.post(
            "/tasks/schedule-scraping",
            json={"portal": "JustJoinIT"},
        )
        assert response.status_code == 422

    def test_response_has_correct_structure(self, test_client, mock_async_drf_client):
        response = test_client.post("/tasks/schedule-scraping", json={})
        data = response.json()
        assert "task_id" in data
        assert "message" in data
        assert "status_url" in data
        assert "/tasks/status/" in data["status_url"]


class TestAPIHealth:
    def test_openapi_endpoint(self, test_client):
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

    def test_docs_endpoint(self, test_client):
        response = test_client.get("/docs")
        assert response.status_code == 200


class TestTaskScheduleResponseSchema:
    def test_response_model_example(self, test_client, mock_async_drf_client):
        response = test_client.post("/tasks/schedule-scraping", json={})
        data = response.json()
        task_id = data["task_id"]
        assert len(task_id) == 36
        assert "-" in task_id
