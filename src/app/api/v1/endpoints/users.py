from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.feature.user.models import UserRole
from app.feature.user.schemas import UserProfileResponse

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.get("/me", response_model=UserProfileResponse)
async def read_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
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
