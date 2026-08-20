from unittest.mock import AsyncMock

import pytest

from app.feature.course import service
from tests.api.factories import CourseFactory, LessonFactory


async def test_upload_lesson_file_creates_asset_and_two_jobs(monkeypatch):
    lesson = LessonFactory(id=1, course=CourseFactory(id=1, instructor_id=7))
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = lambda obj: None
    session.add_all = lambda objs: None

    monkeypatch.setattr(service, "get_lesson_by_id", AsyncMock(return_value=lesson))
    monkeypatch.setattr(
        service, "get_course_by_id", AsyncMock(return_value=lesson.course)
    )
    monkeypatch.setattr(service, "get_next_asset_version", AsyncMock(return_value=1))

    asset, subtitle_job, finalize_job = await service.upload_lesson_file(
        session,
        lesson_id=1,
        user_id=7,
        file_url="lessons/video/abc.mp4",
        checksum="deadbeef",
        content_type="video/mp4",
        size=1024,
    )

    assert asset.lesson_id == 1
    assert asset.version == 1
    assert asset.storage_key == "lessons/video/abc.mp4"
    assert subtitle_job.job_type == "subtitle"
    assert subtitle_job.status == "queued"
    assert finalize_job.job_type == "finalize"
    assert finalize_job.status == "queued"


async def test_upload_lesson_file_raises_for_missing_lesson(monkeypatch):
    session = AsyncMock()
    monkeypatch.setattr(service, "get_lesson_by_id", AsyncMock(return_value=None))

    with pytest.raises(ValueError, match="Lesson not found"):
        await service.upload_lesson_file(
            session,
            lesson_id=1,
            user_id=7,
            file_url="x",
            checksum="x",
            content_type="x",
            size=1,
        )


async def test_upload_lesson_file_raises_for_non_instructor(monkeypatch):
    lesson = LessonFactory(id=1, course=CourseFactory(id=1, instructor_id=7))
    session = AsyncMock()
    monkeypatch.setattr(service, "get_lesson_by_id", AsyncMock(return_value=lesson))
    monkeypatch.setattr(
        service, "get_course_by_id", AsyncMock(return_value=lesson.course)
    )

    with pytest.raises(PermissionError):
        await service.upload_lesson_file(
            session,
            lesson_id=1,
            user_id=99,
            file_url="x",
            checksum="x",
            content_type="x",
            size=1,
        )
