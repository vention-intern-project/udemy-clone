import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.review.models import Review
from app.feature.review.schemas import ReviewCreate, ReviewUpdate, ReviewListResponse, ReviewResponse
from app.feature.review.repository import (get_course_reviews, get_review_by_id, get_rating_stats, get_student_review,
                                           delete_rev)

from app.feature.course.repository import get_course_by_id

from app.feature.cart.repository import enrollment_exists


async def create_review(
        session: AsyncSession,
        student_id: int,
        course_id: int,
        data = ReviewCreate,
):
    course = await get_course_by_id(session, course_id)

    if not course:
        raise ValueError("Course not found")

    enrolled = await enrollment_exists(session, student_id, course_id)

    if not enrolled:
        raise PermissionError("Only enrolled students can review courses")

    existing = await get_student_review(
        session,
        student_id,
        course_id,
    )

    if existing:
        raise PermissionError("You already have reviewed this course")

    review = Review(
        user_id=student_id,
        course_id=course_id,
        rating=data.rating,
        comment=data.comment,
    )

    session.add(review)
    await session.commit()
    await session.refresh(review)

    return review

async def update_review(
        session: AsyncSession,
        review_id: int,
        student_id: int,
        data = ReviewUpdate,
):

    review = await get_review_by_id(session, review_id)

    if review is None:
        raise ValueError("Review not found")

    if review.user_id != student_id:
        raise PermissionError("Not allowed")

    if data.rating is not None:
        review.rating = data.rating

    if data.comment is not None:
        review.comment = data.comment

    await session.commit()
    await session.refresh(review)

    return review

async def delete_review_service(
        session: AsyncSession,
        review_id: int,
        student_id: int,
):

    review = await get_review_by_id(session, review_id)

    if review is None:
        raise ValueError("Review not found")

    if review.user_id != student_id:
        raise PermissionError("Not allowed")

    await delete_rev(session, review)


async def get_course_reviews_service(
    session: AsyncSession,
    course_id: int,
    page: int = 1,
    page_size: int = 20,
):
    reviews, total = await get_course_reviews(
        session,
        course_id,
        page,
        page_size,
    )

    pages = math.ceil(total / page_size)

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(review) for review in reviews],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_previous=page > 1,
    )

async def get_rating(
    session: AsyncSession,
    course_id: int,
):
    return await get_rating_stats(
        session,
        course_id,
    )