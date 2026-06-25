from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.feature.course.models import Course, Lesson


async def get_course_by_id(session: AsyncSession, course_id: int) -> Course | None:
    result = await session.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def get_course_with_lessons(
    session: AsyncSession, course_id: int
) -> Course | None:
    result = await session.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(joinedload(Course.instructor), selectinload(Course.lessons))
    )
    return result.scalar_one_or_none()


async def get_lesson_by_id(session: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await session.execute(
        select(Lesson)
        .options(selectinload(Lesson.course))
        .where(Lesson.id == lesson_id)
    )
    return result.scalar_one_or_none()


async def delete_course(session: AsyncSession, course: Course) -> None:
    await session.delete(course)
    await session.commit()


async def delete_lesson(session: AsyncSession, lesson: Lesson) -> None:
    await session.delete(lesson)
    await session.commit()


async def get_all_courses(session: AsyncSession) -> list[Course]:
    result = await session.execute(
        select(Course).options(
            joinedload(Course.instructor), selectinload(Course.lessons)
        )
    )
    return list(result.scalars().all())
