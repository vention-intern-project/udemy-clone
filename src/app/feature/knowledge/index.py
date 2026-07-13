from datetime import date
from pathlib import Path

import aiofiles

from app.core.config import settings


def get_knowledge_root() -> Path:
    return Path(settings.MEDIA_ROOT) / "knowledge"


def ensure_directories(course_id: int) -> tuple[Path, Path]:
    root = get_knowledge_root()
    course_dir = root / "courses" / str(course_id) / "lessons"
    course_dir.mkdir(parents=True, exist_ok=True)
    return root, course_dir


def get_general_index_path() -> Path:
    return get_knowledge_root() / "INDEX.md"


def get_course_index_path(course_id: int) -> Path:
    return get_knowledge_root() / "courses" / str(course_id) / "INDEX.md"


def get_lesson_path(course_id: int, lesson_id: int) -> Path:
    return (
        get_knowledge_root()
        / "courses"
        / str(course_id)
        / "lessons"
        / f"{lesson_id}.txt"
    )


async def read_index(path: Path) -> str:
    if path.exists():
        async with aiofiles.open(path) as f:
            return await f.read()
    return ""


async def write_index(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w") as f:
        await f.write(content)


def parse_table_rows(content: str) -> list[dict]:
    rows = []
    for line in content.splitlines():
        if (
            line.startswith("|")
            and not line.startswith("| Course ID")
            and not line.startswith("| Lesson ID")
            and not line.startswith("|---")
        ):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if cells:
                rows.append(cells)
    return rows


async def update_general_index(
    course_id: int,
    title: str,
    description: str,
    lesson_count: int,
) -> None:
    path = get_general_index_path()
    content = await read_index(path)

    if not content:
        content = (
            "# Knowledge Base\n\n"
            "| Course ID | Title | Description | Lessons | Updated |\n"
            "|-----------|-------|-------------|---------|---------|\n"
        )

    lines = content.splitlines()
    new_lines = []
    found = False

    for line in lines:
        if line.startswith(f"| {course_id} |"):
            today = date.today().isoformat()
            row = (
                f"| {course_id} | {title} | {description} | {lesson_count} | {today} |"
            )
            new_lines.append(row)
            found = True
        else:
            new_lines.append(line)

    if not found:
        today = date.today().isoformat()
        row = f"| {course_id} | {title} | {description} | {lesson_count} | {today} |"
        new_lines.append(row)

    await write_index(path, "\n".join(new_lines) + "\n")


async def update_course_index(
    course_id: int,
    course_title: str,
    lesson_id: int,
    lesson_title: str,
    keywords: list[str],
    description: str,
) -> None:
    path = get_course_index_path(course_id)
    content = await read_index(path)

    if not content:
        content = (
            f"# Course: {course_title}\n\n"
            "| Lesson ID | Title | Keywords | Description |\n"
            "|-----------|-------|----------|-------------|\n"
        )

    keyword_str = ", ".join(keywords)
    lines = content.splitlines()
    new_lines = []
    found = False

    for line in lines:
        if line.startswith(f"| {lesson_id} |"):
            new_lines.append(
                f"| {lesson_id} | {lesson_title} | {keyword_str} | {description} |"
            )
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(
            f"| {lesson_id} | {lesson_title} | {keyword_str} | {description} |"
        )

    await write_index(path, "\n".join(new_lines) + "\n")


async def remove_lesson_from_index(course_id: int, lesson_id: int) -> None:
    path = get_course_index_path(course_id)
    content = await read_index(path)
    if not content:
        return

    lines = content.splitlines()
    new_lines = [line for line in lines if not line.startswith(f"| {lesson_id} |")]
    await write_index(path, "\n".join(new_lines) + "\n")


async def remove_course_from_general_index(course_id: int) -> None:
    path = get_general_index_path()
    content = await read_index(path)
    if not content:
        return

    lines = content.splitlines()
    new_lines = [line for line in lines if not line.startswith(f"| {course_id} |")]
    await write_index(path, "\n".join(new_lines) + "\n")


async def list_courses_from_index() -> list[dict]:
    content = await read_index(get_general_index_path())
    if not content:
        return []

    rows = parse_table_rows(content)
    courses = []
    for row in rows:
        if len(row) >= 4:
            courses.append(
                {
                    "course_id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "lessons": row[3],
                }
            )
    return courses


async def list_lessons_from_index(course_id: int) -> list[dict]:
    content = await read_index(get_course_index_path(course_id))
    if not content:
        return []

    rows = parse_table_rows(content)
    lessons = []
    for row in rows:
        if len(row) >= 4:
            lessons.append(
                {
                    "lesson_id": row[0],
                    "title": row[1],
                    "keywords": row[2],
                    "description": row[3],
                }
            )
    return lessons
