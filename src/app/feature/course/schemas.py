from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CourseUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instructor_id: int
    title: str
    description: str | None
    price: Decimal
    currency: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
