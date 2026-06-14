from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.feature.user.models import User
from app.feature.user.repository import get_user_by_email, get_user_by_id
from app.feature.user.schemas import UserRegister


async def get_user_profile(session: AsyncSession, user_id: int) -> User | None:
    return await get_user_by_id(session, user_id)


async def register_user(
    session: AsyncSession,
    user_data: UserRegister,
):

    existing_user = await get_user_by_email(session, user_data.email)

    if existing_user:
        raise ValueError("User already exists")

    user = User(
        email=user_data.email,
        name=user_data.name,
        surname=user_data.surname,
        password=user_data.password,
        role=user_data.role,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})

    return {"user": user, "access_token": token, "token_type": "bearer"}
