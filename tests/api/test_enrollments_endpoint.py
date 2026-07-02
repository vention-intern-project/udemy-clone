from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import enrollments
from app.db.database import get_db
from app.feature.enrollment.schemas import (
    CourseSummary,
    EnrollmentListResponse,
    EnrollmentResponse,
)
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
def mock_enroll_service(monkeypatch):
    enroll_mock = AsyncMock()
    monkeypatch.setattr(enrollments, "enroll_in_course", enroll_mock)
    return enroll_mock


@pytest.fixture
def mock_my_enrollments_service(monkeypatch):
    list_mock = AsyncMock()
    monkeypatch.setattr(enrollments, "get_my_enrollments", list_mock)
    return list_mock


@pytest.fixture
def mock_enrollment_detail_service(monkeypatch):
    detail_mock = AsyncMock()
    monkeypatch.setattr(enrollments, "get_enrollment_detail", detail_mock)
    return detail_mock


@pytest.fixture
def free_course_response():
    return EnrollmentResponse(
        id=1,
        user_id=1,
        course_id=1,
        status="active",
        created_at="2026-07-02T12:00:00Z",
        updated_at="2026-07-02T12:00:00Z",
        course=CourseSummary(
            id=1,
            title="Python 101",
            description="Intro to Python",
            price=0,
            currency="UZS",
        ),
    )


@pytest.fixture
def paid_course_response():
    return EnrollmentResponse(
        id=2,
        user_id=1,
        course_id=2,
        status="pending_payment",
        created_at="2026-07-02T12:00:00Z",
        updated_at="2026-07-02T12:00:00Z",
        course=CourseSummary(
            id=2,
            title="Advanced Django",
            description="Deep dive",
            price=49.99,
            currency="USD",
        ),
    )


@pytest.fixture
def empty_list_response():
    return EnrollmentListResponse(
        items=[],
        page=1,
        page_size=100,
        total=0,
        pages=0,
        has_next=False,
        has_previous=False,
    )


# --- POST /enrollments ---


def test_enroll_in_free_course(client, mock_enroll_service, free_course_response):
    mock_enroll_service.return_value = free_course_response

    response = client.post(
        "/enrollments",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"
    assert data["course"]["price"] == "0"


def test_enroll_in_paid_course(client, mock_enroll_service, paid_course_response):
    mock_enroll_service.return_value = paid_course_response

    response = client.post(
        "/enrollments",
        json={"course_id": 2},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending_payment"
    assert data["course"]["price"] == "49.99"


def test_enroll_nonexistent_course(client, mock_enroll_service):
    mock_enroll_service.side_effect = LookupError("Course not found")

    response = client.post(
        "/enrollments",
        json={"course_id": 999},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_enroll_unpublished_course(client, mock_enroll_service):
    mock_enroll_service.side_effect = ValueError("Course is not published")

    response = client.post(
        "/enrollments",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Course is not published"}


def test_enroll_already_enrolled(client, mock_enroll_service):
    mock_enroll_service.side_effect = ValueError("Already enrolled in this course")

    response = client.post(
        "/enrollments",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Already enrolled in this course"}


def test_enroll_non_student(client, mock_enroll_service):
    mock_enroll_service.side_effect = PermissionError(
        "Only students can enroll in courses"
    )

    response = client.post(
        "/enrollments",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Only students can enroll in courses"}


def test_enroll_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.post("/enrollments", json={"course_id": 1})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# --- GET /enrollments/my ---


def test_list_my_enrollments(client, mock_my_enrollments_service, empty_list_response):
    mock_my_enrollments_service.return_value = empty_list_response

    response = client.get(
        "/enrollments/my",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_list_my_enrollments_empty(
    client, mock_my_enrollments_service, empty_list_response
):
    mock_my_enrollments_service.return_value = empty_list_response

    response = client.get(
        "/enrollments/my",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# --- GET /enrollments/{id} ---


def test_get_enrollment_detail(
    client, mock_enrollment_detail_service, free_course_response
):
    mock_enrollment_detail_service.return_value = free_course_response

    response = client.get(
        "/enrollments/1",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "active"


def test_get_enrollment_not_found(client, mock_enrollment_detail_service):
    mock_enrollment_detail_service.side_effect = LookupError("Enrollment not found")

    response = client.get(
        "/enrollments/999",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Enrollment not found"}


def test_get_enrollment_not_own(client, mock_enrollment_detail_service):
    mock_enrollment_detail_service.side_effect = PermissionError(
        "You do not have access to this enrollment"
    )

    response = client.get(
        "/enrollments/1",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this enrollment"}
