from unittest.mock import MagicMock

from app.tasks import uploads
from tests.api.factories import LessonAssetFactory, ProcessingJobFactory


class FakeSessionLocal:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    def __enter__(self):
        return self._session

    def __exit__(self, *args):
        return False


def make_session(get_result):
    session = MagicMock()
    session.get.return_value = get_result
    return session


def test_finalize_upload_marks_ready_for_valid_file(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1, storage_key="lessons/video/abc.mp4")
    job = ProcessingJobFactory(id=1, asset=asset, job_type="finalize", status="queued")

    (tmp_path / "lessons" / "video").mkdir(parents=True)
    (tmp_path / "lessons" / "video" / "abc.mp4").write_bytes(b"content")

    session = make_session(job)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1)

    assert job.status == "completed"
    assert job.failure_reason is None


def test_finalize_upload_marks_failed_for_missing_file(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1, storage_key="lessons/video/missing.mp4")
    job = ProcessingJobFactory(id=1, asset=asset, job_type="finalize", status="queued")

    session = make_session(job)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1)

    assert job.status == "failed"
    assert job.failure_reason == "Uploaded file is missing or empty"


def test_finalize_upload_noop_when_job_missing(monkeypatch, tmp_path):
    session = make_session(None)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1)

    session.commit.assert_not_called()


def test_finalize_upload_noop_when_job_type_mismatched(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1)
    job = ProcessingJobFactory(id=1, asset=asset, job_type="subtitle", status="queued")

    session = make_session(job)
    monkeypatch.setattr(uploads, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(uploads, "get_media_root", lambda: tmp_path)

    uploads.finalize_lesson_upload(1)

    session.commit.assert_not_called()
