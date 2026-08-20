import hashlib

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id, optional_current_user_id
from app.core.storage import delete_file, get_media_root, save_file
from app.db.database import get_db
from app.feature.course.models import LessonType
from app.feature.course.schemas import (
    LessonResponse,
    LessonUpdateRequest,
    LessonUploadResponse,
    LessonUploadStatusResponse,
)
from app.feature.course.service import (
    get_lesson_detail,
    get_lesson_upload_status,
    update_lesson,
    upload_lesson_file,
)
from app.feature.enrollment.repository import get_active_enrollment_by_course
from app.feature.knowledge.service import process_lesson_upload
from app.tasks.subtitles import generate_subtitles
from app.tasks.uploads import finalize_lesson_upload

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    user_id: int | None = Depends(optional_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    lesson = await get_lesson_detail(session, lesson_id)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    response = LessonResponse.model_validate(lesson)

    if user_id is not None:
        is_instructor = lesson.course.instructor_id == user_id
        if not is_instructor:
            enrollment = await get_active_enrollment_by_course(
                session, user_id, lesson.course_id
            )
            if enrollment is None:
                response.download_url = None
    else:
        response.download_url = None

    return response


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


@router.get("/uploads/{upload_id}/status", response_model=LessonUploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        asset = await get_lesson_upload_status(session, upload_id, user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        ) from None

    jobs_by_type = {job.job_type: job for job in asset.jobs}
    subtitle_status = jobs_by_type.get("subtitle")
    finalize_status = jobs_by_type.get("finalize")

    statuses = [job.status for job in asset.jobs]
    if "failed" in statuses:
        overall = "failed"
    elif any(s != "completed" for s in statuses):
        overall = "processing" if any(s == "processing" for s in statuses) else "queued"
    else:
        overall = "ready"

    failure_reason = next(
        (job.failure_reason for job in asset.jobs if job.status == "failed"), None
    )
    latest_update = max(
        (job.updated_at for job in asset.jobs), default=asset.created_at
    )

    return LessonUploadStatusResponse(
        upload_id=asset.upload_id,
        lesson_id=asset.lesson_id,
        version=asset.version,
        status=overall,
        subtitle_status=subtitle_status.status if subtitle_status else None,
        finalize_status=finalize_status.status if finalize_status else None,
        failure_reason=failure_reason,
        updated_at=latest_update,
    )


@router.post("/{lesson_id}/upload-file", response_model=LessonUploadResponse)
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

    try:
        file_url = await save_file(file, lesson_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    written_path = get_media_root() / file_url
    file_bytes = written_path.read_bytes()

    try:
        asset, subtitle_job, finalize_job = await upload_lesson_file(
            session,
            lesson_id,
            user_id,
            file_url,
            checksum=hashlib.sha256(file_bytes).hexdigest(),
            content_type=file.content_type or "application/octet-stream",
            size=len(file_bytes),
        )
        if lesson.lesson_type == LessonType.VIDEO:
            generate_subtitles.delay(subtitle_job.id)
        finalize_lesson_upload.delay(finalize_job.id)
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

    return LessonUploadResponse(
        lesson_id=lesson_id,
        upload_id=asset.upload_id,
        status="queued",
        detail="File accepted and queued for processing",
    )
