from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.course.schemas import (
    CourseCreateRequest,
    CourseDetailResponse,
    CourseResponse,
    CourseUpdateRequest,
    DeleteMessageResponse,
    LessonCreateRequest,
    LessonResponse,
)
from app.feature.course.service import (
    create_course,
    create_lesson,
    deleting_course,
    deleting_lesson,
    get_course_detail,
    update_course,
)
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id

router = APIRouter(prefix="/courses", tags=["courses"])


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
