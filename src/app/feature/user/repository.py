from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.user.models import User, PasswordResetToken


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, user_email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == user_email))
    return result.scalar_one_or_none()


async def create_reset_token(session: AsyncSession, user_id: int, token: str, expires_at) -> PasswordResetToken | None:
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )

    session.add(reset_token)
    await session.commit()

    return reset_token


async def get_by_reset_token(session: AsyncSession, token: str) -> PasswordResetToken | None:
    result = await session.execute(select(PasswordResetToken).where(PasswordResetToken.token == token))

    return result.scalar_one_or_none()

async def mark_reset_token_as_used(session: AsyncSession, reset_token: PasswordResetToken) -> None:
    reset_token.used = True
    await session.commit()