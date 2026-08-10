from unittest.mock import MagicMock

from app.feature.course.models import UploadStatusType
from app.tasks import uploads
from tests.api.factories import LessonFactory


class FakeSessionLocal:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    def __enter__(self):
        return self._session

    def __exit__(self, *args):
        return False


def make_session(scalar_result_or_side_effect):
    session = MagicMock()
    if callable(scalar_result_or_side_effect):
        session.scalar.side_effect = scalar_result_or_side_effect
    else:
        session.scalar.return_value = scalar_result_or_side_effect
    return session


def test_finalize_upload_marks_ready_for_valid_file(monkeypatch, tmp_path):
    lesson = LessonFactory(
        id=1,
        file_url="lessons/video/abc.mp4",
        upload_id="gen-1",
        upload_status=UploadStatusType.QUEUED,
    )
    (tmp_path / "lessons" / "video").mkdir(parents=True)
    (tmp_path / "lessons" / "video" / "abc.mp4").write_bytes(b"content")

    session = make_session(lesson)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1, "gen-1")

    assert lesson.upload_status == UploadStatusType.READY
    assert lesson.upload_failure_reason is None


def test_finalize_upload_marks_failed_for_missing_file(monkeypatch, tmp_path):
    lesson = LessonFactory(
        id=1,
        file_url="lessons/video/missing.mp4",
        upload_id="gen-1",
        upload_status=UploadStatusType.QUEUED,
    )

    session = make_session(lesson)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1, "gen-1")

    assert lesson.upload_status == UploadStatusType.FAILED
    assert lesson.upload_failure_reason == "Uploaded file is missing or empty"


def test_finalize_upload_noop_when_lesson_missing(monkeypatch, tmp_path):
    session = make_session(None)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1, "gen-1")

    session.commit.assert_not_called()


def test_finalize_upload_noop_when_superseded_by_newer_upload(monkeypatch, tmp_path):
    lesson = LessonFactory(
        id=1,
        file_url="lessons/video/abc.mp4",
        upload_id="gen-2",
        upload_status=UploadStatusType.QUEUED,
    )

    session = make_session(lesson)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1, "gen-1")

    session.commit.assert_not_called()
    assert lesson.upload_status == UploadStatusType.QUEUED


def test_finalize_upload_noop_when_superseded_mid_task(monkeypatch, tmp_path):
    lesson = LessonFactory(
        id=1,
        file_url="lessons/video/abc.mp4",
        upload_id="gen-1",
        upload_status=UploadStatusType.QUEUED,
    )
    (tmp_path / "lessons" / "video").mkdir(parents=True)
    (tmp_path / "lessons" / "video" / "abc.mp4").write_bytes(b"content")

    calls = {"n": 0}

    def scalar_side_effect(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            lesson.upload_id = "gen-2"
        return lesson

    session = make_session(scalar_side_effect)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1, "gen-1")

    assert lesson.upload_status == UploadStatusType.PROCESSING
