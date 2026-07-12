from pathlib import Path

import aiofiles

from app.core.config import settings
from app.feature.knowledge.extraction import extract_text
from app.feature.knowledge.index import (
    ensure_directories,
    get_course_index_path,
    get_general_index_path,
    get_lesson_path,
    parse_table_rows,
    read_index,
    remove_lesson_from_index,
    update_course_index,
    update_general_index,
)
from app.feature.knowledge.metadata import generate_metadata


def get_file_path(file_url: str) -> Path:
    return Path(settings.MEDIA_ROOT) / file_url


async def _persist_lesson(
    course_id: int,
    lesson_id: int,
    lesson_title: str,
    course_title: str,
    content: str,
) -> None:
    metadata = await generate_metadata(content)
    lesson_path = get_lesson_path(course_id, lesson_id)
    async with aiofiles.open(lesson_path, "w") as f:
        await f.write(f"# {lesson_title}\n\n{content}")
    await update_course_index(
        course_id,
        course_title,
        lesson_id,
        lesson_title,
        metadata["keywords"],
        metadata["description"],
    )
    await _update_general_index_count(course_id, course_title)


async def process_lesson_upload(
    course_id: int,
    lesson_id: int,
    lesson_title: str,
    lesson_type: str,
    file_url: str | None,
    course_title: str,
    description: str | None = None,
) -> None:
    ensure_directories(course_id)

    if not file_url:
        if description:
            await _persist_lesson(
                course_id, lesson_id, lesson_title, course_title, description
            )
        return

    file_path = get_file_path(file_url)
    if not file_path.exists():
        return

    content = extract_text(file_path, lesson_type)
    await _persist_lesson(course_id, lesson_id, lesson_title, course_title, content)


async def _update_general_index_count(course_id: int, course_title: str) -> None:
    course_index_path = get_course_index_path(course_id)
    course_content = await read_index(course_index_path)
    lesson_count = len(parse_table_rows(course_content))

    general_path = get_general_index_path()
    general_content = await read_index(general_path)
    existing_description = ""
    for row in parse_table_rows(general_content):
        if len(row) >= 3 and row[0] == str(course_id):
            existing_description = row[2]
            break

    await update_general_index(
        course_id, course_title, existing_description, lesson_count
    )


async def process_lesson_update(
    course_id: int,
    lesson_id: int,
    lesson_title: str,
    lesson_type: str,
    file_url: str | None,
    course_title: str,
    description: str | None = None,
) -> None:
    await process_lesson_upload(
        course_id,
        lesson_id,
        lesson_title,
        lesson_type,
        file_url,
        course_title,
        description,
    )


async def process_lesson_delete(course_id: int, lesson_id: int) -> None:
    lesson_path = get_lesson_path(course_id, lesson_id)
    if lesson_path.exists():
        lesson_path.unlink()

    await remove_lesson_from_index(course_id, lesson_id)
