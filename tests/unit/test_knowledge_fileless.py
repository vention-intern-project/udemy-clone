from app.core.config import settings
from app.feature.knowledge import service
from app.feature.knowledge.index import get_course_index_path, get_lesson_path


async def fake_metadata(content):
    return {"keywords": ["notes", "reading"], "description": "A lesson."}


async def test_published_fileless_lesson_is_ingested(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Reading List",
        course_title="Python 101",
        description="Chapters 1 through 4.",
        is_published=True,
        has_file=False,
    )

    written = get_lesson_path(1, 5).read_text()
    assert written.startswith("# Reading List")
    assert "Chapters 1 through 4." in written

    rows = [
        line
        for line in get_course_index_path(1).read_text().splitlines()
        if line.startswith("| 5 |")
    ]
    assert len(rows) == 1


async def test_lesson_with_file_is_left_alone(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.ingest_lesson_text(
        course_id=1,
        lesson_id=5,
        lesson_title="Recorded Talk",
        course_title="Python 101",
        content="the real whisper transcript",
    )
    before = get_lesson_path(1, 5).read_text()

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Recorded Talk",
        course_title="Python 101",
        description="a description edited three weeks later",
        is_published=True,
        has_file=True,
    )

    assert get_lesson_path(1, 5).read_text() == before


async def test_unpublished_lesson_with_file_is_not_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.ingest_lesson_text(
        course_id=1,
        lesson_id=5,
        lesson_title="Recorded Talk",
        course_title="Python 101",
        content="the real whisper transcript",
    )

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Recorded Talk",
        course_title="Python 101",
        description=None,
        is_published=False,
        has_file=True,
    )

    assert get_lesson_path(1, 5).exists()
    assert "the real whisper transcript" in get_lesson_path(1, 5).read_text()


async def test_unpublished_fileless_lesson_is_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Draft",
        course_title="Python 101",
        description="work in progress",
        is_published=True,
        has_file=False,
    )
    assert get_lesson_path(1, 5).exists()

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Draft",
        course_title="Python 101",
        description="work in progress",
        is_published=False,
        has_file=False,
    )

    assert not get_lesson_path(1, 5).exists()
    rows = [
        line
        for line in get_course_index_path(1).read_text().splitlines()
        if line.startswith("| 5 |")
    ]
    assert rows == []


async def test_cleared_description_removes_lesson(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Notes",
        course_title="Python 101",
        description="some notes",
        is_published=True,
        has_file=False,
    )

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Notes",
        course_title="Python 101",
        description="",
        is_published=True,
        has_file=False,
    )

    assert not get_lesson_path(1, 5).exists()


async def test_never_ingested_draft_is_a_noop(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    await service.sync_lesson_knowledge(
        course_id=1,
        lesson_id=5,
        lesson_title="Draft",
        course_title="Python 101",
        description=None,
        is_published=False,
        has_file=False,
    )

    assert not get_lesson_path(1, 5).exists()


async def test_resync_replaces_content(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "generate_metadata", fake_metadata)

    for text in ("first version", "second version"):
        await service.sync_lesson_knowledge(
            course_id=1,
            lesson_id=5,
            lesson_title="Notes",
            course_title="Python 101",
            description=text,
            is_published=True,
            has_file=False,
        )

    written = get_lesson_path(1, 5).read_text()
    assert "second version" in written
    assert "first version" not in written

    rows = [
        line
        for line in get_course_index_path(1).read_text().splitlines()
        if line.startswith("| 5 |")
    ]
    assert len(rows) == 1
