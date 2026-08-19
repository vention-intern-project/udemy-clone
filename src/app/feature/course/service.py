import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import delete_file
from app.feature.course.models import Course, Lesson, LessonAsset, ProcessingJob
from app.feature.course.repository import (
    delete_course,
    delete_lesson,
    get_all_courses,
    get_asset_by_upload_id,
    get_course_by_id,
    get_course_with_lessons,
    get_lesson_by_id,
    get_next_asset_version,
    list_lessons,
)
from app.feature.course.schemas import (
    CourseCreateRequest,
    CourseFilters,
    CourseListItemResponse,
    CourseListResponse,
    CourseUpdateRequest,
    LessonBriefResponse,
    LessonCreateRequest,
    LessonListItemResponse,
    LessonListResponse,
    LessonUpdateRequest,
)
from app.feature.knowledge.service import process_lesson_delete
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id


async def is_admin_user(session: AsyncSession, viewer_id: int | None) -> bool:
    if viewer_id is None:
        return False

    viewer = await get_user_by_id(session, viewer_id)

    return viewer is not None and viewer.role == UserRole.ADMIN


async def can_view_unpublished_lessons(
    session: AsyncSession,
    viewer_id: int | None,
    instructor_id: int | None,
) -> bool:
    """Only the owning instructor and admins may see draft lessons."""
    if viewer_id is None:
        return False

    if instructor_id is not None and viewer_id == instructor_id:
        return True

    return await is_admin_user(session, viewer_id)


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


async def upload_lesson_file(
    session: AsyncSession,
    lesson_id: int,
    user_id: int,
    file_url: str,
    checksum: str,
    content_type: str,
    size: int,
) -> tuple[LessonAsset, ProcessingJob, ProcessingJob]:
    lesson = await get_lesson_by_id(session, lesson_id)

    if lesson is None:
        raise ValueError("Lesson not found")

    course = await get_course_by_id(session, lesson.course_id)

    if course is None or course.instructor_id != user_id:
        raise PermissionError(
            "You do not have permission to upload files to this lesson."
        )

    version = await get_next_asset_version(session, lesson_id)
    asset = LessonAsset(
        lesson_id=lesson_id,
        upload_id=uuid.uuid4().hex,
        version=version,
        storage_key=file_url,
        checksum=checksum,
        content_type=content_type,
        size=size,
    )
    session.add(asset)
    await session.flush()

    subtitle_job = ProcessingJob(
        asset_id=asset.id, job_type="subtitle", status="queued"
    )
    finalize_job = ProcessingJob(
        asset_id=asset.id, job_type="finalize", status="queued"
    )
    session.add_all([subtitle_job, finalize_job])

    await session.commit()
    await session.refresh(asset)
    return asset, subtitle_job, finalize_job


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

    for asset in lesson.assets:
        delete_file(asset.storage_key)

    await process_lesson_delete(lesson.course_id, lesson.id)

    await delete_lesson(session, lesson)

    return "Lesson deleted successfully"


async def get_courses_list(
    session: AsyncSession,
    page: int,
    page_size: int,
    filters: CourseFilters,
    viewer_id: int | None = None,
    instructor_id: int | None = None,
) -> CourseListResponse:
    courses, total = await get_all_courses(
        session, page, page_size, filters, instructor_id=instructor_id
    )

    is_admin = await is_admin_user(session, viewer_id)

    items = []
    for course in courses:
        item = CourseListItemResponse.model_validate(course)

        if not (is_admin or course.instructor_id == viewer_id):
            item.lessons = [
                LessonBriefResponse.model_validate(lesson)
                for lesson in course.lessons
                if lesson.is_published
            ]

        items.append(item)

    pages = math.ceil(total / page_size)

    return CourseListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_previous=page > 1,
    )


async def get_lesson_upload_status(
    session: AsyncSession,
    upload_id: str,
    user_id: int,
) -> LessonAsset:
    asset = await get_asset_by_upload_id(session, upload_id)

    if asset is None:
        raise ValueError("Upload not found")

    is_admin = await is_admin_user(session, user_id)

    if asset.lesson.course.instructor_id != user_id and not is_admin:
        raise ValueError("Upload not found")

    return asset


async def get_list_lessons(
    session: AsyncSession,
    course_id: int,
    page: int,
    size: int,
    include_unpublished: bool = False,
):
    lessons, total = await list_lessons(
        session,
        course_id=course_id,
        page=page,
        size=size,
        include_unpublished=include_unpublished,
    )

    pages = math.ceil(total / size)

    return LessonListResponse(
        items=[LessonListItemResponse.model_validate(lesson) for lesson in lessons],
        page=page,
        page_size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_previous=page > 1,
    )
