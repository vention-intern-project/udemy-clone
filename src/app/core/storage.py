import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}
MAX_PDF_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150 MB


def get_media_root() -> Path:
    from app.core.config import settings

    return Path(settings.MEDIA_ROOT)


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_file_type(filename: str, lesson_type: str) -> None:
    ext = get_file_extension(filename)
    if lesson_type == "video" and ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"Invalid file type for video lesson. Allowed: "
            f"{', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )
    if lesson_type == "pdf" and ext not in ALLOWED_PDF_EXTENSIONS:
        raise ValueError(
            f"Invalid file type for PDF lesson. Allowed: "
            f"{', '.join(ALLOWED_PDF_EXTENSIONS)}"
        )


def validate_file_size(size: int, lesson_type: str) -> None:
    max_size = MAX_VIDEO_SIZE if lesson_type == "video" else MAX_PDF_SIZE
    if size > max_size:
        max_mb = max_size // (1024 * 1024)
        raise ValueError(f"File size exceeds maximum of {max_mb} MB")


def generate_filename(original_filename: str) -> str:
    ext = get_file_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


async def save_file(file: UploadFile, lesson_type: str) -> str:
    if not file.filename:
        raise ValueError("No filename provided")

    validate_file_type(file.filename, lesson_type)

    media_root = get_media_root()
    type_dir = media_root / "lessons" / lesson_type
    type_dir.mkdir(parents=True, exist_ok=True)

    filename = generate_filename(file.filename)
    file_path = type_dir / filename

    content = await file.read()
    validate_file_size(len(content), lesson_type)

    with open(file_path, "wb") as f:
        f.write(content)

    return f"lessons/{lesson_type}/{filename}"


def delete_file(file_url: str) -> None:
    media_root = get_media_root()
    file_path = media_root / file_url
    if file_path.exists():
        file_path.unlink()
