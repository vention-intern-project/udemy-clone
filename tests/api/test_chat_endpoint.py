from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_chat_agent, get_current_user_id
from app.api.v1.endpoints import chat
from app.db.database import get_db
from app.main import app


@pytest.fixture
def client():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = lambda: 1
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_get_course(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(chat, "get_course_by_id", mock)
    return mock


@pytest.fixture
def mock_get_lesson(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(chat, "get_lesson_by_id", mock)
    return mock


@pytest.fixture
def mock_get_enrollment(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(chat, "get_active_enrollment_by_course", mock)
    return mock


@pytest.fixture
def course():
    obj = MagicMock()
    obj.id = 1
    return obj


@pytest.fixture
def lesson():
    obj = MagicMock()
    obj.id = 1
    obj.course_id = 1
    return obj


@pytest.fixture
def enrollment():
    obj = MagicMock()
    obj.id = 1
    return obj


@pytest.fixture(autouse=True)
def mock_agent(client):
    agent = AsyncMock()
    msg = MagicMock()
    msg.text = "Hello! How can I help?"
    agent.ainvoke.return_value = {"messages": [msg]}
    app.dependency_overrides[get_chat_agent] = lambda: agent
    yield agent
    app.dependency_overrides.pop(get_chat_agent, None)


# --- POST /chat/ ---


def test_chat_without_course_or_lesson(client):
    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "message": "What courses do you have?",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "test-thread-123"
    assert data["response"] == "Hello! How can I help?"


def test_chat_with_course_only(
    client,
    mock_get_course,
    mock_get_enrollment,
    course,
    enrollment,
):
    mock_get_course.return_value = course
    mock_get_enrollment.return_value = enrollment

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 1,
            "message": "Summarize this course",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello! How can I help?"


def test_chat_with_course_and_lesson(
    client,
    mock_get_course,
    mock_get_lesson,
    mock_get_enrollment,
    course,
    lesson,
    enrollment,
):
    mock_get_course.return_value = course
    mock_get_lesson.return_value = lesson
    mock_get_enrollment.return_value = enrollment

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 1,
            "lesson_id": 1,
            "message": "Explain this lesson",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello! How can I help?"


def test_chat_course_not_found(client, mock_get_course):
    mock_get_course.return_value = None

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 999,
            "message": "Hello",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_chat_lesson_not_found(client, mock_get_course, mock_get_lesson, course):
    mock_get_course.return_value = course
    mock_get_lesson.return_value = None

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 1,
            "lesson_id": 999,
            "message": "Hello",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}


def test_chat_lesson_wrong_course(client, mock_get_course, mock_get_lesson, course):
    mock_get_course.return_value = course
    wrong_lesson = MagicMock()
    wrong_lesson.id = 2
    wrong_lesson.course_id = 999
    mock_get_lesson.return_value = wrong_lesson

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 1,
            "lesson_id": 2,
            "message": "Hello",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}


def test_chat_not_enrolled(
    client,
    mock_get_course,
    mock_get_enrollment,
    course,
):
    mock_get_course.return_value = course
    mock_get_enrollment.return_value = None

    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
            "course_id": 1,
            "message": "Hello",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this course"}


def test_chat_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.post(
            "/chat/",
            json={
                "thread_id": "test-thread-123",
                "message": "Hello",
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_chat_validation_error(client):
    response = client.post(
        "/chat/",
        json={
            "thread_id": "test-thread-123",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422


def test_chat_missing_thread_id(client):
    response = client.post(
        "/chat/",
        json={
            "message": "Hello",
        },
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
