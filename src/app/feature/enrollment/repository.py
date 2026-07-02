from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.feature.enrollment.models import Enrollment, EnrollmentStatus


async def create_enrollment(
    session: AsyncSession,
    user_id: int,
    course_id: int,
    status: EnrollmentStatus,
) -> Enrollment:
    enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id,
        status=status,
    )
    session.add(enrollment)
    await session.commit()
    await session.refresh(enrollment)
    return enrollment


async def get_enrollment_by_user_and_course(
    session: AsyncSession,
    user_id: int,
    course_id: int,
) -> Enrollment | None:
    result = await session.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
    )
    return result.scalar_one_or_none()


async def get_enrollments_by_user(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[Enrollment], int]:
    offset = (page - 1) * page_size

    query = (
        select(Enrollment)
        .options(selectinload(Enrollment.course))
        .where(Enrollment.user_id == user_id)
        .order_by(Enrollment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    enrollments = list(result.scalars().all())

    count_stmt = (
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.user_id == user_id)
    )
    total = await session.scalar(count_stmt)

    return enrollments, total


async def get_enrollment_by_id(
    session: AsyncSession,
    enrollment_id: int,
) -> Enrollment | None:
    result = await session.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.course))
        .where(Enrollment.id == enrollment_id)
    )
    return result.scalar_one_or_none()


async def get_enrollments_by_course(
    session: AsyncSession,
    course_id: int,
    page: int,
    page_size: int,
) -> tuple[list[Enrollment], int]:
    offset = (page - 1) * page_size

    query = (
        select(Enrollment)
        .options(selectinload(Enrollment.user))
        .where(Enrollment.course_id == course_id)
        .order_by(Enrollment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(query)
    enrollments = list(result.scalars().all())

    count_stmt = (
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.course_id == course_id)
    )
    total = await session.scalar(count_stmt)

    return enrollments, total
