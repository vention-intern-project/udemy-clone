from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.models import Course
from app.feature.course.repository import get_course_by_id
from app.feature.course.schemas import CourseUpdateRequest


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
