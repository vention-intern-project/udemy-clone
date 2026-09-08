from app.core.config import settings
from app.feature.knowledge import service
from app.feature.knowledge.index import get_lesson_path


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
