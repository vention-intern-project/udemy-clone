from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import dependencies
from app.api.v1.dependencies import get_current_user_id, optional_current_user_id
from app.api.v1.endpoints import courses
from app.db.database import get_db
from app.feature.course import service as course_service
from app.feature.course.models import LessonType, SubtitleStatusType
from app.feature.course.schemas import (
    CourseListItemResponse,
    CourseListResponse,
    InstructorResponse,
    LessonBriefResponse,
    LessonListItemResponse,
    LessonListResponse,
)
from app.feature.user.models import UserRole
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
    assert arg_page_size == 24
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
    assert arg_page_size == 24
    assert arg_filters.search_query is None


def test_list_courses_search_empty_result(
    client, mock_list_service, empty_list_response
):
    mock_list_service.return_value = empty_list_response

    response = client.get("/courses?query=nonexistent")

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.fixture
def mock_user_lookup(monkeypatch):
    """Patch the viewer lookup used by the draft-visibility checks."""
    get_user_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(course_service, "get_user_by_id", get_user_mock)
    return get_user_mock


@pytest.fixture
def mock_list_repository(monkeypatch, mock_user_lookup):
    """Patch the repository calls so the real get_courses_list service runs."""
    get_all_mock = AsyncMock()
    monkeypatch.setattr(course_service, "get_all_courses", get_all_mock)
    return get_all_mock, mock_user_lookup


@pytest.fixture
def course_with_draft_lesson():
    instructor = UserFactory(name="Jane", surname="Doe")
    published = [LessonFactory(is_published=True) for _ in range(3)]
    draft = LessonFactory(title="Draft lesson", is_published=False)
    return (
        CourseFactory(instructor=instructor, lessons=[*published, draft]),
        draft,
    )


def lesson_titles(response):
    return [lesson["title"] for lesson in response.json()["items"][0]["lessons"]]


def test_list_courses_hides_drafts_from_anonymous(
    client, mock_list_repository, course_with_draft_lesson
):
    get_all, _ = mock_list_repository
    course, draft = course_with_draft_lesson
    get_all.return_value = ([course], 1)

    response = client.get("/courses")

    assert response.status_code == 200
    assert len(response.json()["items"][0]["lessons"]) == 3
    assert draft.title not in lesson_titles(response)


def test_list_courses_hides_drafts_from_student(
    client, mock_list_repository, course_with_draft_lesson
):
    get_all, get_user = mock_list_repository
    course, draft = course_with_draft_lesson
    get_all.return_value = ([course], 1)

    student = UserFactory(name="Sam", role=UserRole.STUDENT)
    get_user.return_value = student
    app.dependency_overrides[optional_current_user_id] = lambda: student.id

    response = client.get("/courses")

    assert response.status_code == 200
    assert len(response.json()["items"][0]["lessons"]) == 3
    assert draft.title not in lesson_titles(response)


def test_list_courses_shows_drafts_to_owning_instructor(
    client, mock_list_repository, course_with_draft_lesson
):
    get_all, get_user = mock_list_repository
    course, draft = course_with_draft_lesson
    get_all.return_value = ([course], 1)

    get_user.return_value = course.instructor
    app.dependency_overrides[optional_current_user_id] = lambda: course.instructor_id

    response = client.get("/courses")

    assert response.status_code == 200
    assert len(response.json()["items"][0]["lessons"]) == 4
    assert draft.title in lesson_titles(response)


def test_list_courses_shows_drafts_to_admin(
    client, mock_list_repository, course_with_draft_lesson
):
    get_all, get_user = mock_list_repository
    course, draft = course_with_draft_lesson
    get_all.return_value = ([course], 1)

    admin = UserFactory(name="Root", role=UserRole.ADMIN)
    get_user.return_value = admin
    app.dependency_overrides[optional_current_user_id] = lambda: admin.id

    response = client.get("/courses")

    assert response.status_code == 200
    assert len(response.json()["items"][0]["lessons"]) == 4
    assert draft.title in lesson_titles(response)


def test_list_courses_skips_user_lookup_for_anonymous(
    client, mock_list_repository, course_with_draft_lesson
):
    get_all, get_user = mock_list_repository
    course, _ = course_with_draft_lesson
    get_all.return_value = ([course], 1)

    response = client.get("/courses")

    assert response.status_code == 200
    get_user.assert_not_awaited()


def detail_lesson_titles(response):
    return [lesson["title"] for lesson in response.json()["lessons"]]


def test_get_course_hides_drafts_from_anonymous(
    client, mock_service, mock_user_lookup, course_with_draft_lesson
):
    get_detail, _ = mock_service
    course, draft = course_with_draft_lesson
    get_detail.return_value = course

    response = client.get("/courses/1")

    assert response.status_code == 200
    assert len(response.json()["lessons"]) == 3
    assert draft.title not in detail_lesson_titles(response)
    mock_user_lookup.assert_not_awaited()


def test_get_course_shows_drafts_to_owning_instructor(
    client, mock_service, mock_user_lookup, course_with_draft_lesson
):
    get_detail, _ = mock_service
    course, draft = course_with_draft_lesson
    get_detail.return_value = course

    app.dependency_overrides[optional_current_user_id] = lambda: course.instructor_id

    response = client.get("/courses/1")

    assert response.status_code == 200
    assert len(response.json()["lessons"]) == 4
    assert draft.title in detail_lesson_titles(response)


def test_get_course_shows_drafts_to_admin(
    client, mock_service, mock_user_lookup, course_with_draft_lesson
):
    get_detail, _ = mock_service
    course, draft = course_with_draft_lesson
    get_detail.return_value = course

    admin = UserFactory(name="Root", role=UserRole.ADMIN)
    mock_user_lookup.return_value = admin
    app.dependency_overrides[optional_current_user_id] = lambda: admin.id

    response = client.get("/courses/1")

    assert response.status_code == 200
    assert len(response.json()["lessons"]) == 4
    assert draft.title in detail_lesson_titles(response)


@pytest.fixture
def mock_lessons_service(monkeypatch):
    get_course_mock = AsyncMock()
    list_mock = AsyncMock()
    monkeypatch.setattr(courses, "get_course_by_id", get_course_mock)
    monkeypatch.setattr(courses, "get_list_lessons", list_mock)

    list_mock.return_value = LessonListResponse(
        items=[
            LessonListItemResponse(
                id=1,
                title="Intro",
                lesson_type=LessonType.PDF,
                download_url="/media/lessons/secret.pdf",
                subtitle_status=SubtitleStatusType.PENDING,
                subtitles_path=None,
                transcript_path=None,
                description=None,
                is_published=True,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ],
        page=1,
        page_size=100,
        total=1,
        pages=1,
        has_next=False,
        has_previous=False,
    )
    return get_course_mock, list_mock


def include_unpublished_arg(list_mock):
    return list_mock.call_args.kwargs["include_unpublished"]


def test_list_lessons_excludes_drafts_for_anonymous(
    client, mock_lessons_service, mock_user_lookup
):
    get_course, list_lessons_mock = mock_lessons_service
    get_course.return_value = CourseFactory()

    response = client.get("/courses/1/lessons")

    assert response.status_code == 200
    assert include_unpublished_arg(list_lessons_mock) is False
    mock_user_lookup.assert_not_awaited()


def test_list_lessons_hides_download_url_from_anonymous(
    client, mock_lessons_service, mock_user_lookup
):
    get_course, _ = mock_lessons_service
    get_course.return_value = CourseFactory()

    response = client.get("/courses/1/lessons")

    assert response.status_code == 200
    assert response.json()["items"][0]["download_url"] is None


def test_list_lessons_includes_drafts_for_owning_instructor(
    client, mock_lessons_service, mock_user_lookup
):
    get_course, list_lessons_mock = mock_lessons_service
    course = CourseFactory()
    get_course.return_value = course

    app.dependency_overrides[optional_current_user_id] = lambda: course.instructor_id

    response = client.get("/courses/1/lessons")

    assert response.status_code == 200
    assert include_unpublished_arg(list_lessons_mock) is True
    assert response.json()["items"][0]["download_url"] == "/media/lessons/secret.pdf"


def test_list_lessons_includes_drafts_for_admin(
    client, mock_lessons_service, mock_user_lookup
):
    get_course, list_lessons_mock = mock_lessons_service
    get_course.return_value = CourseFactory()

    admin = UserFactory(name="Root", role=UserRole.ADMIN)
    mock_user_lookup.return_value = admin
    app.dependency_overrides[optional_current_user_id] = lambda: admin.id

    response = client.get("/courses/1/lessons")

    assert response.status_code == 200
    assert include_unpublished_arg(list_lessons_mock) is True


def test_list_lessons_excludes_drafts_for_student(
    client, mock_lessons_service, mock_user_lookup
):
    get_course, list_lessons_mock = mock_lessons_service
    get_course.return_value = CourseFactory()

    student = UserFactory(name="Sam", role=UserRole.STUDENT)
    mock_user_lookup.return_value = student
    app.dependency_overrides[optional_current_user_id] = lambda: student.id

    response = client.get("/courses/1/lessons")

    assert response.status_code == 200
    assert include_unpublished_arg(list_lessons_mock) is False


@pytest.fixture
def mock_instructor_lookup(monkeypatch):
    """Patch the user lookup behind the get_current_instructor dependency."""
    get_user_mock = AsyncMock(return_value=UserFactory(role=UserRole.INSTRUCTOR))
    monkeypatch.setattr(dependencies, "get_user_by_id", get_user_mock)
    return get_user_mock


@pytest.fixture
def mock_create_course_service(monkeypatch):
    create_mock = AsyncMock(return_value=CourseFactory())
    monkeypatch.setattr(courses, "create_course", create_mock)
    return create_mock


def test_create_course_allows_instructor(
    client, mock_instructor_lookup, mock_create_course_service
):
    response = client.post(
        "/courses",
        json={"title": "New course", "price": "10.00", "currency": "USD"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert mock_create_course_service.await_count == 1


def test_create_course_rejects_student(
    client, mock_instructor_lookup, mock_create_course_service
):
    mock_instructor_lookup.return_value = UserFactory(role=UserRole.STUDENT)

    response = client.post(
        "/courses",
        json={"title": "New course", "price": "10.00", "currency": "USD"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert mock_create_course_service.await_count == 0


def test_create_course_rejects_token_of_deleted_user(
    client, mock_instructor_lookup, mock_create_course_service
):
    mock_instructor_lookup.return_value = None

    response = client.post(
        "/courses",
        json={"title": "New course", "price": "10.00", "currency": "USD"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert mock_create_course_service.await_count == 0


def test_create_course_rejects_missing_title(
    client, mock_instructor_lookup, mock_create_course_service
):
    """title is NOT NULL at the DB level; the schema must reject it first."""
    response = client.post(
        "/courses",
        json={"price": "10.00", "currency": "USD"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
    assert mock_create_course_service.await_count == 0


def test_list_my_courses_scopes_to_the_authenticated_instructor(
    client, mock_instructor_lookup, mock_list_service, empty_list_response
):
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    mock_instructor_lookup.return_value = instructor
    mock_list_service.return_value = empty_list_response

    response = client.get(
        "/courses/my",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert mock_list_service.await_args.kwargs["instructor_id"] == instructor.id
    assert mock_list_service.await_args.kwargs["viewer_id"] == instructor.id


def test_list_my_courses_ignores_instructor_id_query_param(
    client, mock_instructor_lookup, mock_list_service, empty_list_response
):
    """Ownership comes from the token, so a forged query param must not widen it."""
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    mock_instructor_lookup.return_value = instructor
    mock_list_service.return_value = empty_list_response

    response = client.get(
        "/courses/my?instructor_id=999999",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert mock_list_service.await_args.kwargs["instructor_id"] == instructor.id


def test_list_my_courses_returns_page_metadata(
    client, mock_instructor_lookup, mock_list_service
):
    instructor = UserFactory(role=UserRole.INSTRUCTOR)
    mock_instructor_lookup.return_value = instructor
    course = CourseFactory(instructor=instructor, lessons=[LessonFactory()])
    mock_list_service.return_value = CourseListResponse(
        items=[CourseListItemResponse.model_validate(course)],
        page=1,
        page_size=20,
        total=1,
        pages=1,
        has_next=False,
        has_previous=False,
    )

    response = client.get(
        "/courses/my",
        headers={"Authorization": "Bearer valid-token"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["items"][0]["id"] == course.id
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["has_next"] is False
    assert body["has_previous"] is False


def test_list_my_courses_defaults_to_first_page_of_twenty(
    client, mock_instructor_lookup, mock_list_service, empty_list_response
):
    mock_list_service.return_value = empty_list_response

    client.get("/courses/my", headers={"Authorization": "Bearer valid-token"})

    assert mock_list_service.await_args.args[1] == 1
    assert mock_list_service.await_args.args[2] == 20


def test_list_my_courses_rejects_page_below_one(
    client, mock_instructor_lookup, mock_list_service
):
    response = client.get(
        "/courses/my?page=0",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
    assert mock_list_service.await_count == 0


def test_list_my_courses_rejects_page_size_above_the_cap(
    client, mock_instructor_lookup, mock_list_service
):
    response = client.get(
        "/courses/my?page_size=101",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
    assert mock_list_service.await_count == 0


def test_list_my_courses_rejects_student(
    client, mock_instructor_lookup, mock_list_service
):
    mock_instructor_lookup.return_value = UserFactory(role=UserRole.STUDENT)

    response = client.get(
        "/courses/my",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Only instructors can access this resource"}
    assert mock_list_service.await_count == 0


def test_list_my_courses_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.get("/courses/my")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.fixture
def mock_create_lesson_service(monkeypatch):
    create_mock = AsyncMock(return_value=LessonFactory())
    monkeypatch.setattr(courses, "create_lesson", create_mock)
    return create_mock


def test_create_lesson_rejects_missing_title(client, mock_create_lesson_service):
    """title is NOT NULL at the DB level; the schema must reject it first."""
    response = client.post(
        "/courses/1/lessons",
        json={"lesson_type": "video"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
    assert mock_create_lesson_service.await_count == 0


def test_create_lesson_rejects_missing_lesson_type(client, mock_create_lesson_service):
    """lesson_type is NOT NULL at the DB level; the schema must reject it first."""
    response = client.post(
        "/courses/1/lessons",
        json={"title": "Intro"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
    assert mock_create_lesson_service.await_count == 0


def test_create_lesson_course_not_found_returns_404(client, mock_create_lesson_service):
    mock_create_lesson_service.side_effect = ValueError("Course not found")

    response = client.post(
        "/courses/1/lessons",
        json={"title": "Intro", "lesson_type": "video"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


@pytest.fixture
def mock_delete_course_service(monkeypatch):
    delete_mock = AsyncMock(return_value="Course deleted successfully")
    monkeypatch.setattr(courses, "deleting_course", delete_mock)
    return delete_mock


def test_delete_course_not_found_returns_404(client, mock_delete_course_service):
    mock_delete_course_service.side_effect = ValueError("Course not found")

    response = client.delete(
        "/courses/1", headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_delete_course_permission_denied(client, mock_delete_course_service):
    msg = "You do not have permission to delete this course."
    mock_delete_course_service.side_effect = PermissionError(msg)

    response = client.delete(
        "/courses/1", headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": msg}


@pytest.fixture
def mock_delete_lesson_service(monkeypatch):
    delete_mock = AsyncMock(return_value="Lesson deleted successfully")
    monkeypatch.setattr(courses, "deleting_lesson", delete_mock)
    return delete_mock


def test_delete_lesson_not_found_returns_404(client, mock_delete_lesson_service):
    mock_delete_lesson_service.side_effect = ValueError("Lesson not found")

    response = client.delete(
        "/courses/1/lessons/1", headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Lesson not found"}


def test_delete_lesson_permission_denied(client, mock_delete_lesson_service):
    msg = "You do not have permission to delete the classes of this course."
    mock_delete_lesson_service.side_effect = PermissionError(msg)

    response = client.delete(
        "/courses/1/lessons/1", headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": msg}
