from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EnrollmentCreate(BaseModel):
    course_id: int


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    currency: str


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    course: CourseSummary
