import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.repository import get_course_by_id, get_lesson_by_id, count_course_lessons
from app.feature.enrollment.models import EnrollmentStatus
from app.feature.enrollment.repository import (
    create_enrollment,
    get_enrollment_by_id,
    get_enrollment_by_user_and_course,
    get_enrollments_by_course,
    get_enrollments_by_user,
    get_progress,
    complete_progress,
    incomplete_progress,
    count_completed_lessons,
    create_progress,
)
from app.feature.enrollment.schemas import (
    CourseEnrollmentListResponse,
    CourseEnrollmentResponse,
    CourseSummary,
    EnrollmentListResponse,
    EnrollmentResponse,
    StudentSummary,
    CourseProgressResponse,
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


async def get_enrollment_detail(
    session: AsyncSession,
    enrollment_id: int,
    user_id: int,
) -> EnrollmentResponse:
    enrollment = await get_enrollment_by_id(session, enrollment_id)

    if enrollment is None:
        raise LookupError("Enrollment not found")

    if enrollment.user_id != user_id:
        raise PermissionError("You do not have access to this enrollment")

    return EnrollmentResponse(
        id=enrollment.id,
        user_id=enrollment.user_id,
        course_id=enrollment.course_id,
        status=enrollment.status.value,
        created_at=enrollment.created_at,
        updated_at=enrollment.updated_at,
        course=CourseSummary.model_validate(enrollment.course),
    )


async def get_course_enrollments(
    session: AsyncSession,
    course_id: int,
    instructor_id: int,
    page: int,
    page_size: int,
) -> CourseEnrollmentListResponse:
    course = await get_course_by_id(session, course_id)
    if course is None:
        raise LookupError("Course not found")

    if course.instructor_id != instructor_id:
        raise PermissionError(
            "You do not have permission to view enrollments for this course"
        )

    enrollments, total = await get_enrollments_by_course(
        session, course_id, page, page_size
    )
    pages = math.ceil(total / page_size) if total > 0 else 0

    return CourseEnrollmentListResponse(
        items=[
            CourseEnrollmentResponse(
                id=e.id,
                user_id=e.user_id,
                course_id=e.course_id,
                status=e.status.value,
                created_at=e.created_at,
                updated_at=e.updated_at,
                user=StudentSummary.model_validate(e.user),
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


async def complete_lesson(
    session: AsyncSession,
    student_id: int,
    lesson_id: int,
    course_id: int,
):

    lesson = await get_lesson_by_id(session, lesson_id)

    if lesson is None:
        raise LookupError("Lesson not found")

    if lesson.course.id != course_id:
        raise PermissionError("This lesson does not belong to this course.")

    enrollment = await get_enrollment_by_user_and_course(session, student_id, course_id)

    if enrollment is None:
        raise LookupError("Enrollment not found")

    progress = await get_progress(session, student_id, lesson_id)

    if progress is None:
        return await create_progress(session, student_id, lesson_id)

    if not progress.completed:
        return await complete_progress(session, progress)

    return progress


async def incomplete_lesson(
    session: AsyncSession,
    student_id: int,
    lesson_id: int,
    course_id: int,
):

    lesson = await get_lesson_by_id(session, lesson_id)

    if lesson is None:
        raise LookupError("Lesson not found")

    if lesson.course.id != course_id:
        raise PermissionError("This lesson does not belong to this course.")

    enrollment = await get_enrollment_by_user_and_course(session, student_id, course_id)

    if enrollment is None:
        raise LookupError("Enrollment not found")

    progress = await get_progress(session, student_id, lesson_id)

    if progress is None:
        raise LookupError("This lesson is not tracked yet")

    if progress.completed:
        return await incomplete_progress(session, progress)

    return progress


async def course_progress(
    session: AsyncSession,
    student_id: int,
    course_id: int,
) -> CourseProgressResponse:
    enrollment = await get_enrollment_by_user_and_course(session, student_id, course_id)

    if enrollment is None:
        raise LookupError("Enrollment not found")

    total_lessons = await count_course_lessons(session, course_id)

    total_completed_lessons = await count_completed_lessons(session, student_id, course_id)

    percentage = (
        0
        if total_lessons == 0
        else round(total_completed_lessons / total_lessons * 100, 2)
    )

    return CourseProgressResponse(
        course_id=course_id,
        completed_lessons=total_completed_lessons,
        total_lessons=total_lessons,
        progress_percentage=percentage,
    )