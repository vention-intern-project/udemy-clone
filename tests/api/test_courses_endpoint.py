from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import courses
from app.db.database import get_db
from app.feature.course.schemas import (
    CourseListItemResponse,
    CourseListResponse,
    InstructorResponse,
    LessonBriefResponse,
)
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


@pytest.fixture
def empty_list_response():
    return CourseListResponse(
        items=[],
        page=1,
        page_size=10,
        total=0,
        pages=0,
        has_next=False,
        has_previous=False,
    )


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


def test_list_courses_empty(client, mock_list_service, empty_list_response):
    mock_list_service.return_value = empty_list_response

    response = client.get("/courses")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "page": 1,
        "page_size": 10,
        "total": 0,
        "pages": 0,
        "has_next": False,
        "has_previous": False,
    }


def test_list_courses_returns_items(client, mock_list_service):
    lesson = LessonBriefResponse(
        id=1,
        title="Intro",
    )

    instructor = InstructorResponse(
        id=1,
        name="Jane",
        surname="Doe",
    )

    item = CourseListItemResponse(
        id=1,
        title="Python 101",
        description="Intro",
        price=Decimal("9.99"),
        currency="USD",
        published_at=None,
        instructor=instructor,
        lessons=[lesson],
    )

    mock_list_service.return_value = CourseListResponse(
        items=[item],
        page=1,
        page_size=10,
        total=1,
        pages=1,
        has_next=False,
        has_previous=False,
    )

    response = client.get("/courses")

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 1
    assert data["pages"] == 1
    assert data["has_next"] is False
    assert data["has_previous"] is False

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


def test_list_courses_with_search_query(client, mock_list_service, empty_list_response):
    mock_list_service.return_value = empty_list_response

    response = client.get("/courses?search_query=python")

    assert response.status_code == 200

    mock_list_service.assert_called_once()

    _, arg_page, arg_page_size, arg_filters = mock_list_service.call_args.args

    assert arg_page == 1
    assert arg_page_size == 100
    assert arg_filters.search_query == "python"


def test_list_courses_without_query_returns_all(
    client, mock_list_service, empty_list_response
):
    mock_list_service.return_value = empty_list_response

    response = client.get("/courses")

    assert response.status_code == 200

    mock_list_service.assert_called_once()

    _, arg_page, arg_page_size, arg_filters = mock_list_service.call_args.args

    assert arg_page == 1
    assert arg_page_size == 100
    assert arg_filters.search_query is None


def test_list_courses_search_empty_result(
    client, mock_list_service, empty_list_response
):
    mock_list_service.return_value = empty_list_response

    response = client.get("/courses?query=nonexistent")

    assert response.status_code == 200
    assert response.json()["items"] == []
