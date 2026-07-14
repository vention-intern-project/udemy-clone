from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import lessons, media
from app.db.database import get_db
from app.feature.course.models import LessonType
from app.main import app

from .factories import CourseFactory, LessonFactory


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
def no_auth_client():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_upload_service(monkeypatch):
    get_detail_mock = AsyncMock()
    upload_mock = AsyncMock()
    monkeypatch.setattr(lessons, "get_lesson_detail", get_detail_mock)
    monkeypatch.setattr(lessons, "upload_lesson_file", upload_mock)
    return get_detail_mock, upload_mock


@pytest.fixture
def video_lesson():
    return LessonFactory(id=1, lesson_type=LessonType.VIDEO)


def upload_file(
    client,
    lesson_id=1,
    filename="test.mp4",
    content=b"fake content",
    content_type="video/mp4",
):
    return client.post(
        f"/lessons/{lesson_id}/upload-file",
        files={"file": (filename, content, content_type)},
    )


def test_upload_requires_auth(no_auth_client):
    response = upload_file(no_auth_client)
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_upload_instructor_only(client, mock_upload_service, video_lesson):
    get_detail, upload = mock_upload_service
    get_detail.return_value = video_lesson
    upload.side_effect = PermissionError(
        "You do not have permission to upload files to this lesson."
    )

    response = upload_file(client)

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_upload_returns_download_url(
    client, mock_upload_service, video_lesson, monkeypatch
):
    get_detail, upload = mock_upload_service
    get_detail.return_value = video_lesson

    updated_lesson = LessonFactory(
        id=1,
        lesson_type=LessonType.VIDEO,
        file_url="lessons/video/abc123.mp4",
    )
    upload.return_value = updated_lesson

    monkeypatch.setattr(
        lessons, "save_file", AsyncMock(return_value="lessons/video/abc123.mp4")
    )
    monkeypatch.setattr(lessons, "delete_file", MagicMock())

    response = upload_file(
        client, filename="test.mp4", content=b"fake content", content_type="video/mp4"
    )

    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert data["download_url"] == "/media/lessons/abc123.mp4"


def test_upload_wrong_file_type(client, mock_upload_service, video_lesson, monkeypatch):
    get_detail, _ = mock_upload_service
    get_detail.return_value = video_lesson

    monkeypatch.setattr(
        lessons,
        "save_file",
        AsyncMock(
            side_effect=ValueError(
                "Invalid file type for video lesson. Allowed: .mp4, .webm, .mov"
            )
        ),
    )

    response = upload_file(
        client, filename="test.txt", content=b"fake content", content_type="text/plain"
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_download_requires_auth(no_auth_client):
    response = no_auth_client.get("/media/lessons/test.mp4")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_download_returns_file(client, tmp_path, monkeypatch):
    media_dir = tmp_path / "lessons" / "video"
    media_dir.mkdir(parents=True)
    test_file = media_dir / "abc123.mp4"
    test_file.write_bytes(b"fake video content")

    mock_lesson = LessonFactory(
        id=1,
        lesson_type=LessonType.VIDEO,
        file_url="lessons/video/abc123.mp4",
        course=CourseFactory(instructor_id=1),
    )
    monkeypatch.setattr(
        media, "get_lesson_by_file_url", AsyncMock(return_value=mock_lesson)
    )
    monkeypatch.setattr(
        media, "get_active_enrollment_by_course", AsyncMock(return_value=None)
    )

    with patch.object(media, "settings") as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        response = client.get("/media/lessons/abc123.mp4")

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.content == b"fake video content"


def test_download_not_found(client, tmp_path, monkeypatch):
    empty_dir = tmp_path / "lessons"
    empty_dir.mkdir(parents=True)

    monkeypatch.setattr(media, "get_lesson_by_file_url", AsyncMock(return_value=None))

    with patch.object(media, "settings") as mock_settings:
        mock_settings.MEDIA_ROOT = str(tmp_path)
        response = client.get("/media/lessons/nonexistent.mp4")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}
