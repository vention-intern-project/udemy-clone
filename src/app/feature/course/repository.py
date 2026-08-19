from collections.abc import Sequence
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.feature.course.models import Course, Lesson, LessonAsset
from app.feature.course.schemas import CourseFilters
from app.feature.user.models import User

LESSON_ASSET_LOAD_OPTIONS = selectinload(Lesson.assets).selectinload(LessonAsset.jobs)


async def get_course_by_id(session: AsyncSession, course_id: int) -> Course | None:
    result = await session.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def get_course_with_lessons(
    session: AsyncSession, course_id: int
) -> Course | None:
    result = await session.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            joinedload(Course.instructor),
            selectinload(Course.lessons).options(LESSON_ASSET_LOAD_OPTIONS),
        )
    )
    return result.scalar_one_or_none()


async def get_lesson_by_id(session: AsyncSession, lesson_id: int) -> Lesson | None:
    result = await session.execute(
        select(Lesson)
        .options(selectinload(Lesson.course), LESSON_ASSET_LOAD_OPTIONS)
        .where(Lesson.id == lesson_id)
    )
    return result.scalar_one_or_none()


async def get_asset_by_upload_id(
    session: AsyncSession, upload_id: str
) -> LessonAsset | None:
    result = await session.execute(
        select(LessonAsset)
        .options(
            joinedload(LessonAsset.lesson).selectinload(Lesson.course),
            selectinload(LessonAsset.jobs),
        )
        .where(LessonAsset.upload_id == upload_id)
    )
    return result.scalar_one_or_none()


async def get_next_asset_version(session: AsyncSession, lesson_id: int) -> int:
    current_max = await session.scalar(
        select(func.max(LessonAsset.version)).where(LessonAsset.lesson_id == lesson_id)
    )
    return (current_max or 0) + 1


async def delete_course(session: AsyncSession, course: Course) -> None:
    await session.delete(course)
    await session.commit()


async def delete_lesson(session: AsyncSession, lesson: Lesson) -> None:
    await session.delete(lesson)
    await session.commit()


def build_search_condition(search_query: str):
    pattern = f"%{' '.join(search_query.split())}%"

    return or_(
        Course.title.ilike(pattern),
        Course.description.ilike(pattern),
        Course.instructor.has(
            or_(
                func.concat(User.name, " ", User.surname).ilike(pattern),
                func.concat(User.surname, " ", User.name).ilike(pattern),
            )
        ),
    )


async def get_all_courses(
    session: AsyncSession,
    page: int,
    page_size: int,
    filters: CourseFilters,
    instructor_id: int | None = None,
) -> tuple[Sequence[Any], Any | None]:
    offset = (page - 1) * page_size

    filter_conditions = []

    if instructor_id is not None:
        filter_conditions.append(Course.instructor_id == instructor_id)

    if filters.search_query:
        filter_conditions.append(build_search_condition(filters.search_query))

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
            selectinload(Course.lessons).options(LESSON_ASSET_LOAD_OPTIONS),
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
    include_unpublished: bool = False,
) -> tuple[Sequence[Any], Any | None]:
    conditions = [Lesson.course_id == course_id]

    if not include_unpublished:
        conditions.append(Lesson.is_published.is_(True))

    total = await session.scalar(
        select(func.count()).select_from(Lesson).where(*conditions)
    )

    query = (
        select(Lesson)
        .options(LESSON_ASSET_LOAD_OPTIONS)
        .where(*conditions)
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


async def get_lesson_by_storage_key(
    session: AsyncSession, storage_key_suffix: str
) -> Lesson | None:
    result = await session.execute(
        select(Lesson)
        .join(LessonAsset, LessonAsset.lesson_id == Lesson.id)
        .options(selectinload(Lesson.course), LESSON_ASSET_LOAD_OPTIONS)
        .where(LessonAsset.storage_key.ilike(f"%{storage_key_suffix}"))
    )
    return result.scalar_one_or_none()
