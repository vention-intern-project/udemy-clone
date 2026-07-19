from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewCreate(BaseModel):
    rating: float
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: float | None
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    user_id: int
    rating: float | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool
