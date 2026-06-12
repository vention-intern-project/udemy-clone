from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.feature.user.models import UserRole
from app.feature.user.schemas import UserProfileResponse

router = APIRouter()
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


@router.get("/me", response_model=UserProfileResponse)
async def read_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    # Checking is existing bearer
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    # Decoding and checking JWT
    try:
        payload = decode_token(credentials.credentials)
        user_id = _extract_user_id(payload)
        print(user_id)
    except Exception:
        raise _unauthorized() from None

    # Mock user profile
    mock_user_profile = UserProfileResponse(
        email="mmm@example.com",
        name="Mmm",
        surname="Dev",
        role=UserRole.STUDENT,
        birthday=date(1995, 5, 15),
        phone_number="+1234567890",
        created_at=datetime.now(),
    )

    return mock_user_profile
