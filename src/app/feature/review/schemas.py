from pydantic import BaseModel


class ReviewCreate(BaseModel):
    rating: float
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: float | None
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    student_id: int
    rating: float | None
    comment: str | None