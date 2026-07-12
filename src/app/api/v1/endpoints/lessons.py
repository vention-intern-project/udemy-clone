from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.core.storage import delete_file, save_file
from app.db.database import get_db
from app.feature.course.schemas import LessonResponse, LessonUpdateRequest
from app.feature.course.service import (
    get_lesson_detail,
    update_lesson,
    upload_lesson_file,
)
from app.feature.knowledge.service import process_lesson_upload

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


@router.post("/{lesson_id}/upload-file", response_model=LessonResponse)
async def upload_file(
    lesson_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        lesson = await get_lesson_detail(session, lesson_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        ) from None

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    lesson_type = lesson.lesson_type.value
    old_file_url = lesson.file_url

    try:
        file_url = await save_file(file, lesson_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    try:
        updated_lesson = await upload_lesson_file(session, lesson_id, user_id, file_url)
    except PermissionError as e:
        delete_file(file_url)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValueError as e:
        delete_file(file_url)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    if old_file_url:
        delete_file(old_file_url)

    background_tasks.add_task(
        process_lesson_upload,
        course_id=lesson.course_id,
        lesson_id=lesson_id,
        lesson_title=lesson.title,
        lesson_type=lesson_type,
        file_url=file_url,
        course_title=lesson.course.title,
        description=lesson.description,
    )

    return updated_lesson
