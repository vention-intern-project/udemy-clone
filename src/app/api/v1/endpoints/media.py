from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.v1.dependencies import get_current_user_id
from app.core.config import settings

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
):
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
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
