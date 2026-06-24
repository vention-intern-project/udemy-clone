from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.feature.course.schemas import LessonResponse, LessonUpdateRequest
from app.feature.course.service import get_lesson_detail, update_lesson

router = APIRouter(prefix="/lessons", tags=["lessons"])
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
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        token_payload = decode_token(credentials.credentials)
        user_id = _extract_user_id(token_payload)
    except Exception:
        raise _unauthorized() from None

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
