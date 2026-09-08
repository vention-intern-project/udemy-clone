from app.core.config import settings
from app.feature.knowledge import service
from app.feature.knowledge.index import get_course_index_path, get_lesson_path


async def fake_metadata(content):
    return {"keywords": ["python", "loops"], "description": "A lesson."}


async def test_ingest_lesson_text_writes_transcript(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.ingest_lesson_text(
        course_id=1,
        lesson_id=7,
        lesson_title="Intro to Loops",
        course_title="Python 101",
        content="today we cover for loops",
    )

    written = get_lesson_path(1, 7).read_text()
    assert "today we cover for loops" in written
    assert written.startswith("# Intro to Loops")


async def test_reingest_replaces_index_row(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.ingest_lesson_text(
        course_id=1,
        lesson_id=7,
        lesson_title="Intro to Loops",
        course_title="Python 101",
        content="placeholder description",
    )
    await service.ingest_lesson_text(
        course_id=1,
        lesson_id=7,
        lesson_title="Intro to Loops",
        course_title="Python 101",
        content="the real whisper transcript",
    )

    index = get_course_index_path(1).read_text()
    rows = [line for line in index.splitlines() if line.startswith("| 7 |")]
    assert len(rows) == 1
    assert "the real whisper transcript" in get_lesson_path(1, 7).read_text()
    assert "placeholder description" not in get_lesson_path(1, 7).read_text()


async def test_video_upload_uses_description_not_extractor(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.process_lesson_upload(
        course_id=2,
        lesson_id=9,
        lesson_title="Recorded Talk",
        lesson_type="video",
        file_url=None,
        course_title="Public Speaking",
        description="A recorded conference talk.",
    )

    assert "A recorded conference talk." in get_lesson_path(2, 9).read_text()
