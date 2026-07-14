from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.core.config import settings
from app.db.database import get_db
from app.feature.course.repository import get_lesson_by_file_url
from app.feature.enrollment.repository import get_active_enrollment_by_course

router = APIRouter(tags=["media"])

MEDIA_TYPE_MAP = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".pdf": "application/pdf",
}


@router.get("/media/lessons/{filename}")
async def download_lesson_file(
    filename: str,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    lesson = await get_lesson_by_file_url(session, filename)

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    is_instructor = lesson.course.instructor_id == user_id
    enrollment = await get_active_enrollment_by_course(
        session, user_id, lesson.course_id
    )

    if not is_instructor and enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course",
        )

    media_root = Path(settings.MEDIA_ROOT)
    lessons_dir = media_root / "lessons"

    if not lessons_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    for type_dir in lessons_dir.iterdir():
        if type_dir.is_dir():
            file_path = type_dir / filename
            if file_path.is_file():
                content_type = MEDIA_TYPE_MAP.get(
                    file_path.suffix,
                    "application/octet-stream",
                )
                return FileResponse(
                    path=file_path,
                    media_type=content_type,
                    filename=filename,
                )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="File not found",
    )
