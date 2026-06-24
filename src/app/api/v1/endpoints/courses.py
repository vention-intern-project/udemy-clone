from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.feature.course.schemas import CourseResponse, CourseUpdateRequest, CourseCreateRequest
from app.feature.course.service import update_course, create_course
from app.feature.user.repository import get_user_by_id
from app.feature.user.models import UserRole

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


@router.post("/", response_model=CourseResponse)
async def creating_course(
    payload: CourseCreateRequest,
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


@router.patch("/{course_id}", response_model=CourseResponse)
async def patch_course(
    course_id: int,
    payload: CourseUpdateRequest,
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
