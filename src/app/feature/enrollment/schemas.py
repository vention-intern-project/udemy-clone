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


class EnrollmentListResponse(BaseModel):
    items: list[EnrollmentResponse]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class StudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    surname: str
    email: str


class CourseEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    user: StudentSummary


class CourseEnrollmentListResponse(BaseModel):
    items: list[CourseEnrollmentResponse]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class LessonProgressResponse(BaseModel):
    lesson_id: int
    completed: bool
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CourseProgressResponse(BaseModel):
    course_id: int
    completed_lessons: int
    total_lessons: int
    progress_percentage: float
