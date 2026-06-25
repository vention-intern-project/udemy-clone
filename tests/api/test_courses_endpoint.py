from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import courses
from app.db.database import get_db
from app.main import app

from .factories import CourseFactory, LessonFactory, UserFactory


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
def mock_service(monkeypatch):
    get_detail_mock = AsyncMock()
    update_mock = AsyncMock()
    monkeypatch.setattr(courses, "get_course_detail", get_detail_mock)
    monkeypatch.setattr(courses, "update_course", update_mock)
    return get_detail_mock, update_mock


@pytest.fixture
def mock_list_service(monkeypatch):
    list_mock = AsyncMock()
    monkeypatch.setattr(courses, "get_courses_list", list_mock)
    return list_mock


def test_get_course_not_found(client, mock_service):
    get_detail, _ = mock_service
    get_detail.return_value = None

    response = client.get("/courses/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_get_course_returns_detail(client, mock_service):
    get_detail, _ = mock_service
    lesson = LessonFactory()
    instructor = UserFactory(name="Jane", surname="Doe")
    course = CourseFactory(
        instructor=instructor,
        title="Python 101",
        description="Intro",
        lessons=[lesson],
    )
    get_detail.return_value = course

    response = client.get("/courses/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == course.id
    assert data["title"] == "Python 101"
    assert data["instructor"]["name"] == "Jane"
    assert len(data["lessons"]) == 1


def test_patch_course_not_found(client, mock_service):
    _, update = mock_service
    update.return_value = None

    response = client.patch(
        "/courses/1",
        json={"title": "New"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_patch_course_permission_denied(client, mock_service):
    _, update = mock_service
    msg = "You do not have permission to modify this course."
    update.side_effect = PermissionError(msg)

    response = client.patch(
        "/courses/1",
        json={"title": "New"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == msg


def test_patch_course_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.patch("/courses/1", json={"title": "New"})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_list_courses_empty(client, mock_list_service):
    mock_list_service.return_value = []

    response = client.get("/courses")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_list_courses_returns_items(client, mock_list_service):
    lesson = LessonFactory(id=1, title="Intro")
    instructor = UserFactory(name="Jane", surname="Doe")
    course = CourseFactory(
        id=1,
        instructor=instructor,
        title="Python 101",
        description="Intro",
        price=Decimal("9.99"),
        currency="USD",
        lessons=[lesson],
    )
    mock_list_service.return_value = [course]

    response = client.get("/courses")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["id"] == 1
    assert item["title"] == "Python 101"
    assert item["price"] == "9.99"
    assert item["currency"] == "USD"
    assert item["instructor"]["name"] == "Jane"
    assert len(item["lessons"]) == 1
    assert item["lessons"][0]["id"] == 1
    assert item["lessons"][0]["title"] == "Intro"
