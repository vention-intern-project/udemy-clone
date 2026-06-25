from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.course.schemas import (
    CourseCreateRequest,
    CourseResponse,
    CourseUpdateRequest,
    LessonCreateRequest,
    LessonResponse,
)
from app.feature.course.service import create_course, create_lesson, update_course, deleting_lesson, deleting_course
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id

router = APIRouter(prefix="/courses", tags=["courses"])
bearer_scheme = HTTPBearer(auto_error=False)


def _extract_user_id(payload: dict) -> int:
    value = payload.get("id")
    if value is not None:
        return int(value)
    raise ValueError("Token payload does not contain a user identifier")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


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


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dlt_course(
    course_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        await deleting_course(session, course_id, user_id)
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


@router.delete("/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dlt_lesson(
    course_id: int,
    lesson_id: int,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        await deleting_lesson(session, course_id, lesson_id, user_id)
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
