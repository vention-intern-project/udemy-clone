from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Sequence
from typing import Any

from app.feature.review.models import Review


async def get_review_by_id(session: AsyncSession, review_id: int) -> Review | None:
    stmt = select(Review).where(Review.id == review_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_student_review(
        session: AsyncSession,
        student_id: int,
        course_id: int,
) -> Review | None:
    stmt = select(Review).where(
        Review.user_id == student_id,
        Review.course_id == course_id,
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_course_reviews(
        session: AsyncSession,
        course_id: int,
        page: int,
        size: int,
) -> tuple[Sequence[Any], Any | None]:
    stmt = (
        select(Review)
        .where(Review.course_id == course_id)
        .offset((page - 1) * size)
        .limit(size)
        .order_by(Review.created_at.desc())
    )

    total = await session.scalar(
        select(func.count()).select_from(Review).where(Review.course_id == course_id)
    )

    result = await session.execute(stmt)
    return result.scalars().all(), total


async def delete(session: AsyncSession, review: Review):
    await session.delete(review)
    await session.commit()


async def get_rating_stats(session: AsyncSession, course_id: int):
    stmt = select(
        func.avg(Review.rating),
        func.count(Review.id),
    ).where(
        Review.course_id == course_id
    )

    result = await session.execute(stmt)

    average, count = result.one()

    return {
        "average_rating": float(average) if average else 0,
        "review_count": count,
    }