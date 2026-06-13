from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.feature.user.models import UserRole


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    name: str
    surname: str
    role: UserRole
    birthday: date | None
    phone_number: str | None
    created_at: datetime
