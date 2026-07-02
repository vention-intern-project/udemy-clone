from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
