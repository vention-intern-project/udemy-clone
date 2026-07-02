import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.repository import get_course_by_id
from app.feature.enrollment.models import EnrollmentStatus
from app.feature.enrollment.repository import (
    create_enrollment,
    get_enrollment_by_user_and_course,
    get_enrollments_by_user,
)
from app.feature.enrollment.schemas import (
    CourseSummary,
    EnrollmentListResponse,
    EnrollmentResponse,
)
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id


async def enroll_in_course(
    session: AsyncSession,
    user_id: int,
    course_id: int,
) -> EnrollmentResponse:
    user = await get_user_by_id(session, user_id)
    if user.role != UserRole.STUDENT:
        raise PermissionError("Only students can enroll in courses")

    course = await get_course_by_id(session, course_id)
    if course is None:
        raise LookupError("Course not found")

    if course.published_at is None:
        raise ValueError("Course is not published")

    existing = await get_enrollment_by_user_and_course(session, user_id, course_id)
    if existing is not None:
        raise ValueError("Already enrolled in this course")

    status = (
        EnrollmentStatus.ACTIVE
        if course.price == 0
        else EnrollmentStatus.PENDING_PAYMENT
    )

    enrollment = await create_enrollment(session, user_id, course_id, status)
    return EnrollmentResponse(
        id=enrollment.id,
        user_id=enrollment.user_id,
        course_id=enrollment.course_id,
        status=enrollment.status.value,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        course=CourseSummary.model_validate(course),
    )


async def get_my_enrollments(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
) -> EnrollmentListResponse:
    enrollments, total = await get_enrollments_by_user(
        session, user_id, page, page_size
    )
    pages = math.ceil(total / page_size) if total > 0 else 0

    return EnrollmentListResponse(
        items=[
            EnrollmentResponse(
                id=e.id,
                user_id=e.user_id,
                course_id=e.course_id,
                status=e.status.value,
                created_at=e.created_at,
                updated_at=e.updated_at,
                course=CourseSummary.model_validate(e.course),
            )
            for e in enrollments
        ],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_previous=page > 1,
    )
