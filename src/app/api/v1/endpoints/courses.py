from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.course.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CourseFilters,
    CourseListResponse,
    CourseResponse,
    CourseUpdateRequest,
    DeleteMessageResponse,
    LessonCreateRequest,
    LessonListResponse,
    LessonResponse,
)
from app.feature.course.service import (
    create_course,
    create_lesson,
    deleting_course,
    deleting_lesson,
    get_course_detail,
    get_courses_list,
    get_list_lessons,
    update_course,
)
from app.feature.enrollment.schemas import CourseEnrollmentListResponse, LessonProgressResponse, CourseProgressResponse
from app.feature.enrollment.service import get_course_enrollments, complete_lesson, course_progress
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=CourseListResponse)
async def list_courses(
    page: int = 1,
    page_size: int = 100,
    filters: CourseFilters = Depends(),
    session: AsyncSession = Depends(get_db),
):
    return await get_courses_list(session, page, page_size, filters)


@router.post("", response_model=CourseResponse)
async def creating_course(
    payload: CourseCreateRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(session, user_id)

    if user.role != UserRole.INSTRUCTOR:
        raise HTTPException(
            status_code=403,
            detail="Only instructors can create courses",
        )

    try:
        course = await create_course(session, user_id, payload)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return course


@router.get(
    "/{course_id}/lessons",
    response_model=LessonListResponse,
)
async def list_lessons(
    course_id: int,
    page: int = 1,
    size: int = 100,
    session: AsyncSession = Depends(get_db),
):
    return await get_list_lessons(
        session,
        course_id=course_id,
        page=page,
        size=size,
    )


@router.post("/{course_id}/lessons", response_model=LessonResponse)
async def creating_lesson(
    course_id: int,
    payload: LessonCreateRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        lesson = await create_lesson(session, course_id, user_id, payload)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    return lesson


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    session: AsyncSession = Depends(get_db),
):
    course = await get_course_detail(session, course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


@router.get("/{course_id}/enrollments", response_model=CourseEnrollmentListResponse)
async def list_course_enrollments(
    course_id: int,
    page: int = 1,
    page_size: int = 100,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await get_course_enrollments(
            session, course_id, user_id, page, page_size
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return result


@router.patch("/{course_id}", response_model=CourseResponse)
async def patch_course(
    course_id: int,
    payload: CourseUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        course = await update_course(session, course_id, user_id, payload)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


@router.delete("/{course_id}", response_model=DeleteMessageResponse)
async def dlt_course(
    course_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        message = await deleting_course(session, course_id, user_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return DeleteMessageResponse(message=message)


@router.delete("/{course_id}/lessons/{lesson_id}", response_model=DeleteMessageResponse)
async def dlt_lesson(
    course_id: int,
    lesson_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        message = await deleting_lesson(session, course_id, lesson_id, user_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return DeleteMessageResponse(message=message)


@router.post(
    "/{course_id}/lessons/{lesson_id}/complete",
    response_model=LessonProgressResponse,
)
async def completing_lesson(
    course_id: int,
    lesson_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        lesson_progress = await complete_lesson(
            session,
            user_id,
            lesson_id,
            course_id,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return lesson_progress


@router.get(
    "/{course_id}/progress",
    response_model=CourseProgressResponse,
)
async def get_progress(
    course_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        course_progress_bar = await course_progress(
        session,
        user_id,
        course_id,
    )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None

    return course_progress_bar
