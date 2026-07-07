from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.feature.course.models import Lesson
from app.feature.enrollment.models import Enrollment, EnrollmentStatus, LessonProgress


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


async def get_progress(
    session: AsyncSession,
    student_id: int,
    lesson_id: int,
) -> LessonProgress | None:
    stmt = select(LessonProgress).where(
        LessonProgress.student_id == student_id,
        LessonProgress.lesson_id == lesson_id,
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_progress(
    session: AsyncSession,
    student_id: int,
    lesson_id: int,
) -> LessonProgress:

    progress = LessonProgress(
        student_id=student_id,
        lesson_id=lesson_id,
        completed=True,
        completed_at=datetime.utcnow(),
    )

    session.add(progress)
    await session.commit()
    await session.refresh(progress)

    return progress


async def complete_progress(
    session: AsyncSession,
    progress: LessonProgress,
) -> LessonProgress:

    progress.completed = True
    progress.completed_at = datetime.utcnow()

    await session.commit()
    await session.refresh(progress)

    return progress


async def incomplete_progress(
    session: AsyncSession,
    progress: LessonProgress,
) -> LessonProgress:

    progress.completed = False
    progress.completed_at = datetime.utcnow()

    await session.commit()
    await session.refresh(progress)

    return progress


async def count_completed_lessons(
    session: AsyncSession,
    student_id: int,
    course_id: int,
) -> int:

    stmt = (
        select(func.count())
        .select_from(LessonProgress)
        .join(Lesson)
        .where(
            Lesson.course_id == course_id,
            LessonProgress.student_id == student_id,
            LessonProgress.completed.is_(True),
        )
    )

    result = await session.execute(stmt)

    return result.scalar_one()


async def completed_lessons(
    session: AsyncSession,
    student_id: int,
    course_id: int,
) -> list[int]:

    stmt = (
        select(LessonProgress.lesson_id)
        .join(Lesson)
        .where(
            Lesson.course_id == course_id,
            LessonProgress.student_id == student_id,
            LessonProgress.completed.is_(True),
        )
    )

    result = await session.execute(stmt)

    return list(result.scalars())
