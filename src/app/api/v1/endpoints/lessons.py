from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.course.schemas import LessonResponse, LessonUpdateRequest
from app.feature.course.service import get_lesson_detail, update_lesson

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    session: AsyncSession = Depends(get_db),
):
    lesson = await get_lesson_detail(session, lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    return lesson


@router.patch("/{lesson_id}", response_model=LessonResponse)
async def patch_lesson(
    lesson_id: int,
    payload: LessonUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        lesson = await update_lesson(session, lesson_id, user_id, payload)
    except PermissionError as e:
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
