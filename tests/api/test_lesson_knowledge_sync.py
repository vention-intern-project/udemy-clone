from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import courses
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
