from datetime import date, datetime

from fastapi import APIRouter

from app.feature.user.models import UserRole
from app.feature.user.schemas import UserProfileResponse

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def read_current_user():
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
