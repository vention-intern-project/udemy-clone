from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.course.models import Course, Lesson
from app.feature.course.repository import (
    delete_course,
    delete_lesson,
    get_all_courses,
    get_course_by_id,
    get_course_with_lessons,
    get_lesson_by_id,
)
from app.feature.course.schemas import (
    CourseCreateRequest,
    CourseUpdateRequest,
    LessonCreateRequest,
    LessonUpdateRequest,
)


async def create_course(
    session: AsyncSession,
    user_id: int,
    data: CourseCreateRequest,
) -> Course:
    course = Course(
        instructor_id=user_id,
        title=data.title,
        description=data.description,
        price=data.price,
        currency=data.currency,
    )

    session.add(course)
    await session.commit()
    await session.refresh(course)

    return course


async def create_lesson(
    session: AsyncSession,
    course_id: int,
    user_id: int,
    data: LessonCreateRequest,
) -> Lesson:
    course = await get_course_by_id(session, course_id)

    if not course:
        raise ValueError("Course not found")

    if course.instructor_id != user_id:
        raise PermissionError(
            "You do not have permission to add classes to this course."
        )

    lesson = Lesson(
        course_id=course_id,
        title=data.title,
        lesson_type=data.lesson_type,
        description=data.description,
        is_published=data.is_published,
    )

    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)

    return lesson


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


async def update_lesson(
    session: AsyncSession,
    lesson_id: int,
    user_id: int,
    payload: LessonUpdateRequest,
) -> Lesson | None:
    lesson = await get_lesson_by_id(session, lesson_id)

    if lesson is None:
        return None

    course = await get_course_by_id(session, lesson.course_id)

    if course is None or course.instructor_id != user_id:
        raise PermissionError("You do not have permission to modify this lesson.")

    data = payload.model_dump(exclude_unset=True)

    for field_name, value in data.items():
        setattr(lesson, field_name, value)

    await session.commit()
    await session.refresh(lesson)
    return lesson


async def get_lesson_detail(
    session: AsyncSession,
    lesson_id: int,
) -> Lesson | None:
    return await get_lesson_by_id(session, lesson_id)


async def get_course_detail(
    session: AsyncSession,
    course_id: int,
) -> Course | None:
    return await get_course_with_lessons(session, course_id)


async def deleting_course(
    session: AsyncSession,
    course_id: int,
    user_id: int,
) -> str:
    course = await get_course_by_id(session, course_id)

    if not course:
        raise ValueError("Course not found")

    if course.instructor_id != user_id:
        raise PermissionError("You do not have permission to delete this course.")

    await delete_course(session, course)

    return "Course deleted successfully"


async def deleting_lesson(
    session: AsyncSession,
    course_id: int,
    lesson_id: int,
    user_id: int,
) -> str:
    lesson = await get_lesson_by_id(session, lesson_id)

    if not lesson:
        raise ValueError("Lesson not found")

    if lesson.course.id != course_id:
        raise PermissionError("This lesson does not belong to this course.")

    if lesson.course.instructor_id != user_id:
        raise PermissionError(
            "You do not have permission to delete the classes of this course."
        )

    await delete_lesson(session, lesson)

    return "Lesson deleted successfully"


async def get_courses_list(session: AsyncSession) -> list[Course]:
    return await get_all_courses(session)
