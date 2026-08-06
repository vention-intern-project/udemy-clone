from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


Rating = Annotated[float, Field(ge=0.0, le=5.0,
                                description="Rating must be a number between 1 and 5.", examples=[5],)]

class ReviewCreate(BaseModel):
    rating: Rating
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: Rating | None
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    user_id: int
    rating: Rating | None
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
