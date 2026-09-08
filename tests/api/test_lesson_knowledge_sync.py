from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import courses, lessons
from app.db.database import get_db
from app.feature.course.models import LessonType
from app.main import app

from .factories import CourseFactory, LessonAssetFactory, LessonFactory


@pytest.fixture
def client():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = lambda: 1
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_creating_lesson_schedules_knowledge_sync(client, monkeypatch):
    course = CourseFactory(id=3, title="Python 101")
    lesson = LessonFactory(
        id=9,
        course=course,
        title="Reading List",
        lesson_type=LessonType.TEXT,
        description="Chapters 1 through 4.",
        is_published=True,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    monkeypatch.setattr(courses, "create_lesson", AsyncMock(return_value=lesson))
    monkeypatch.setattr(courses, "get_course_by_id", AsyncMock(return_value=course))

    captured = {}

    async def fake_sync(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(courses, "sync_lesson_knowledge", fake_sync)

    response = client.post(
        "/courses/3/lessons",
        json={
            "title": "Reading List",
            "lesson_type": "text",
            "description": "Chapters 1 through 4.",
            "is_published": True,
        },
    )

    assert response.status_code == 200
    assert captured == {
        "course_id": 3,
        "lesson_id": 9,
        "lesson_title": "Reading List",
        "course_title": "Python 101",
        "description": "Chapters 1 through 4.",
        "is_published": True,
        "has_file": False,
    }


def test_patching_fileless_lesson_schedules_sync(client, monkeypatch):
    course = CourseFactory(id=3, title="Python 101")
    lesson = LessonFactory(
        id=9,
        course=course,
        title="Reading List",
        lesson_type=LessonType.TEXT,
        description="Chapters 1 through 6.",
        is_published=True,
    )
    lesson.assets = []

    monkeypatch.setattr(lessons, "update_lesson", AsyncMock(return_value=lesson))

    captured = {}

    async def fake_sync(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(lessons, "sync_lesson_knowledge", fake_sync)

    response = client.patch("/lessons/9", json={"description": "Chapters 1 through 6."})

    assert response.status_code == 200
    assert captured["has_file"] is False
    assert captured["course_id"] == 3
    assert captured["lesson_id"] == 9
    assert captured["course_title"] == "Python 101"
    assert captured["description"] == "Chapters 1 through 6."
    assert captured["is_published"] is True


def test_patching_lesson_with_asset_passes_has_file_true(client, monkeypatch):
    course = CourseFactory(id=3, title="Python 101")
    lesson = LessonFactory(
        id=9,
        course=course,
        title="Recorded Talk",
        lesson_type=LessonType.VIDEO,
        description="edited three weeks later",
        is_published=True,
    )
    lesson.assets = [LessonAssetFactory(id=1, lesson=lesson)]

    monkeypatch.setattr(lessons, "update_lesson", AsyncMock(return_value=lesson))

    captured = {}

    async def fake_sync(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(lessons, "sync_lesson_knowledge", fake_sync)

    response = client.patch(
        "/lessons/9", json={"description": "edited three weeks later"}
    )

    assert response.status_code == 200
    assert captured["has_file"] is True
