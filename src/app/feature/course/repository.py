from collections.abc import Sequence
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.feature.course.models import Course, Lesson
from app.feature.course.schemas import CourseFilters
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
    filters: CourseFilters,
) -> tuple[Sequence[Any], Any | None]:
    offset = (page - 1) * page_size

    filter_conditions = []

    if filters.search_query:
        pattern = f"%{filters.search_query.strip()}%"
        filter_conditions.append(
            or_(
                Course.title.ilike(pattern),
                Course.description.ilike(pattern),
                Course.instructor.has(User.name.ilike(pattern)),
                Course.instructor.has(User.surname.ilike(pattern)),
            )
        )

    if filters.min_price is not None:
        filter_conditions.append(Course.price >= filters.min_price)

    if filters.max_price is not None:
        filter_conditions.append(Course.price <= filters.max_price)

    sort_column = Course.id
    sort_desc = False

    if filters.sort:
        sort_desc = filters.sort.startswith("-")
        sort_field = filters.sort.removeprefix("-")

        sort_mapping = {
            "id": Course.id,
            "title": Course.title,
            "price": Course.price,
            "created_at": Course.created_at,
        }

        if sort_field in sort_mapping:
            sort_column = sort_mapping[sort_field]

    base_query = select(Course)

    if filter_conditions:
        base_query = base_query.where(and_(*filter_conditions))

    query = (
        base_query.options(
            joinedload(Course.instructor),
            selectinload(Course.lessons),
        )
        .order_by(sort_column.desc() if sort_desc else sort_column.asc())
        .offset(offset)
        .limit(page_size)
    )

    result = await session.execute(query)
    courses = result.scalars().all()

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = await session.scalar(count_stmt)

    return courses, total


async def list_lessons(
    session: AsyncSession,
    course_id: int,
    page: int,
    size: int,
) -> tuple[Sequence[Any], Any | None]:
    total = await session.scalar(
        select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
    )

    query = (
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.id)
        .offset((page - 1) * size)
        .limit(size)
    )

    lessons = (await session.scalars(query)).all()

    return lessons, total


async def count_course_lessons(session: AsyncSession, course_id: int) -> int:
    total = await session.scalar(
        select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
    )

    return total