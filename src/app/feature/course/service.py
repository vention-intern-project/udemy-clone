from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.models import Course, Lesson
from app.feature.course.repository import get_course_by_id, get_lesson_by_id
from app.feature.course.schemas import CourseUpdateRequest, LessonUpdateRequest


async def update_course(
    session: AsyncSession,
    course_id: int,
    user_id: int,
    payload: CourseUpdateRequest,
) -> Course | None:
    course = await get_course_by_id(session, course_id)

    if course is None:
        return None

    if course.instructor_id != user_id:
        raise PermissionError("You do not have permission to modify this course.")

    data = payload.model_dump(exclude_unset=True)

    for field_name, value in data.items():
        setattr(course, field_name, value)

    await session.commit()
    await session.refresh(course)
    return course


async def update_lesson(
    session: AsyncSession,
    lesson_id: int,
    user_id: int,
    payload: LessonUpdateRequest,
) -> Lesson | None:
    lesson = await get_lesson_by_id(session, lesson_id)

    if lesson is None:
        return None

    course = await get_course_by_id(session, lesson.course_id)

    if course is None or course.instructor_id != user_id:
        raise PermissionError("You do not have permission to modify this lesson.")

    data = payload.model_dump(exclude_unset=True)

    for field_name, value in data.items():
        setattr(lesson, field_name, value)

    await session.commit()
    await session.refresh(lesson)
    return lesson
