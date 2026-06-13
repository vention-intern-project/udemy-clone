from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.user.models import User


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
