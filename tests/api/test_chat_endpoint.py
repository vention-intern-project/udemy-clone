from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestChatEndpoint:
    def test_chat_endpoint_exists(self):
        response = client.post(
            "/chat/",
            json={
                "thread_id": "test-thread-123",
                "course_id": 1,
                "lesson_id": 1,
                "message": "Hello",
            },
        )
        assert response.status_code in [200, 500]

    def test_chat_endpoint_validation_error(self):
        response = client.post(
            "/chat/",
            json={
                "thread_id": "test-thread-123",
            },
        )
        assert response.status_code == 422

    def test_chat_endpoint_missing_thread_id(self):
        response = client.post(
            "/chat/",
            json={
                "course_id": 1,
                "lesson_id": 1,
                "message": "Hello",
            },
        )
        assert response.status_code == 422
