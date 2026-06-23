from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.models import Course


async def get_course_by_id(session: AsyncSession, course_id: int) -> Course | None:
    result = await session.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()
