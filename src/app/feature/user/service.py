from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.user.models import User
from app.feature.user.repository import get_user_by_id


async def get_user_profile(session: AsyncSession, user_id: int) -> User | None:
    return await get_user_by_id(session, user_id)
