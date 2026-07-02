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
    download_url: str | None
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


class InstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    surname: str


class LessonDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    lesson_type: LessonType
    download_url: str | None
    description: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class CourseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    currency: str
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    instructor: InstructorResponse
    lessons: list[LessonDetailResponse]


class DeleteMessageResponse(BaseModel):
    message: str


class LessonBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str


class CourseListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    currency: str
    published_at: datetime | None
    instructor: InstructorResponse
    lessons: list[LessonBriefResponse]


class CourseListResponse(BaseModel):
    items: list[CourseListItemResponse]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class LessonListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    lesson_type: LessonType
    download_url: str | None
    description: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LessonListResponse(BaseModel):
    items: list[LessonListItemResponse]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class CourseFilters(BaseModel):
    search_query: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    sort: str | None = None
