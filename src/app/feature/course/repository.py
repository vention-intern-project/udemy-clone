from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.feature.course.models import Course, Lesson
from app.feature.user.models import User


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


async def get_all_courses(
    session: AsyncSession,
    page: int,
    page_size: int,
    search_query: str | None = None,
) -> tuple[list[Course], int]:
    offset = (page - 1) * page_size

    filter_condition = None
    search_query = search_query.strip() if search_query else None

    if search_query:
        pattern = f"%{search_query}%"

        filter_condition = or_(
            Course.title.ilike(pattern),
            Course.description.ilike(pattern),
            Course.instructor.has(User.name.ilike(pattern)),
            Course.instructor.has(User.surname.ilike(pattern)),
        )

    base_query = select(Course)
    if filter_condition is not None:
        base_query = base_query.where(filter_condition)

    query = (
        base_query.options(joinedload(Course.instructor), selectinload(Course.lessons))
        .order_by(Course.id)
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    courses = result.scalars().all()

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = await session.scalar(count_stmt)

    return courses, total
