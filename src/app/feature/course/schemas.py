from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.feature.course.models import LessonType


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


class LessonUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    lesson_type: LessonType | None = None
    description: str | None = None
    is_published: bool | None = None


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    lesson_type: LessonType
    file_url: str | None
    description: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class CourseCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class LessonCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    lesson_type: LessonType | None = None
    description: str | None = None
    is_published: bool | None = None


class DeleteMessageResponse(BaseModel):
    message: str