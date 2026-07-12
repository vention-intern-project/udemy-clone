import aiofiles
from langchain_core.tools import tool

from app.feature.knowledge.generation import generate_quiz, generate_summary
from app.feature.knowledge.index import (
    get_course_index_path,
    get_lesson_path,
    list_courses_from_index,
    list_lessons_from_index,
    read_index,
)


@tool
async def list_courses() -> str:
    """List all available courses in the knowledge base."""
    courses = await list_courses_from_index()
    if not courses:
        return "No courses available in the knowledge base."

    lines = ["Available courses:"]
    for c in courses:
        lines.append(
            f"- Course {c['course_id']}: {c['title']}"
            f" ({c['lessons']} lessons) - {c['description']}"
        )
    return "\n".join(lines)


@tool
async def list_lessons(course_id: int) -> str:
    """List all lessons in a specific course."""
    lessons = await list_lessons_from_index(course_id)
    if not lessons:
        return f"No lessons found for course {course_id}."

    lines = [f"Lessons in course {course_id}:"]
    for lesson in lessons:
        lines.append(
            f"- Lesson {lesson['lesson_id']}: {lesson['title']}"
            f" - {lesson['description']}"
        )
    return "\n".join(lines)


@tool
async def read_lesson(course_id: int, lesson_id: int) -> str:
    """Read a specific lesson's content with surrounding context."""
    lesson_path = get_lesson_path(course_id, lesson_id)
    if not lesson_path.exists():
        return f"Lesson {lesson_id} in course {course_id} not found."

    async with aiofiles.open(lesson_path) as f:
        content = await f.read()

    course_index_path = get_course_index_path(course_id)
    course_content = await read_index(course_index_path)

    result = f"## Course Context\n{course_content}\n\n## Lesson Content\n{content}"
    return result


@tool
async def quiz_lesson(course_id: int, lesson_id: int) -> str:
    """Generate a 3-question practice quiz for a lesson."""
    lesson_path = get_lesson_path(course_id, lesson_id)
    if not lesson_path.exists():
        return f"Lesson {lesson_id} in course {course_id} not found."

    async with aiofiles.open(lesson_path) as f:
        content = await f.read()

    questions = await generate_quiz(content)

    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"**Q{i}. {q['question']}**")
        for opt in q["options"]:
            lines.append(f"  {opt}")
        lines.append(f"  Answer: {q['correct_answer']}")
        lines.append("")

    return "\n".join(lines)


@tool
async def summarize_lesson(course_id: int, lesson_id: int) -> str:
    """Generate a summary with paragraph and key takeaways for a lesson."""
    lesson_path = get_lesson_path(course_id, lesson_id)
    if not lesson_path.exists():
        return f"Lesson {lesson_id} in course {course_id} not found."

    async with aiofiles.open(lesson_path) as f:
        content = await f.read()

    summary = await generate_summary(content)

    lines = [summary["paragraph"], "", "**Key Takeaways:**"]
    for bullet in summary["bullets"]:
        lines.append(f"- {bullet}")

    return "\n".join(lines)


KNOWLEDGE_TOOLS = [
    list_courses,
    list_lessons,
    read_lesson,
    quiz_lesson,
    summarize_lesson,
]
