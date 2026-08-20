import contextlib
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.tasks import subtitles
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


def test_generate_subtitles_marks_completed(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1, storage_key="lessons/video/abc.mp4")
    job = ProcessingJobFactory(id=1, asset=asset, job_type="subtitle", status="queued")

    (tmp_path / "lessons" / "video").mkdir(parents=True)
    (tmp_path / "lessons" / "video" / "abc.mp4").write_bytes(b"content")

    session = make_session(job)
    monkeypatch.setattr(subtitles, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(subtitles, "get_media_root", lambda: tmp_path)
    monkeypatch.setattr(
        subtitles,
        "SubtitleService",
        lambda: SimpleNamespace(
            generate=lambda *a, **kw: SimpleNamespace(
                vtt_path="lessons/video/abc.vtt",
                transcript_path="lessons/video/abc.txt",
            )
        ),
    )

    subtitles.generate_subtitles(1)

    assert job.status == "completed"
    assert job.result_path == "lessons/video/abc.vtt"
    assert job.transcript_path == "lessons/video/abc.txt"


def test_generate_subtitles_marks_failed_on_error(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1, storage_key="lessons/video/missing.mp4")
    job = ProcessingJobFactory(id=1, asset=asset, job_type="subtitle", status="queued")

    session = make_session(job)
    monkeypatch.setattr(subtitles, "SessionLocal", FakeSessionLocal(session))
    monkeypatch.setattr(subtitles, "get_media_root", lambda: tmp_path)

    def raise_generate(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        subtitles,
        "SubtitleService",
        lambda: SimpleNamespace(generate=raise_generate),
    )

    with contextlib.suppress(RuntimeError):
        subtitles.generate_subtitles(1)

    assert job.status == "failed"
    assert job.failure_reason == "boom"


def test_generate_subtitles_noop_when_job_missing(monkeypatch, tmp_path):
    session = make_session(None)
    monkeypatch.setattr(subtitles, "SessionLocal", FakeSessionLocal(session))

    subtitles.generate_subtitles(1)

    session.commit.assert_not_called()


def test_generate_subtitles_noop_when_job_type_mismatched(monkeypatch, tmp_path):
    asset = LessonAssetFactory(id=1)
    job = ProcessingJobFactory(id=1, asset=asset, job_type="finalize", status="queued")

    session = make_session(job)
    monkeypatch.setattr(subtitles, "SessionLocal", FakeSessionLocal(session))

    subtitles.generate_subtitles(1)

    session.commit.assert_not_called()
