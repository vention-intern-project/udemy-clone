from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.feature.user.models import User
from app.feature.user.repository import get_user_by_email, get_user_by_id
from app.feature.user.schemas import UserLogin, UserRegister


async def get_user_profile(session: AsyncSession, user_id: int) -> User | None:
    return await get_user_by_id(session, user_id)


async def register_user(
    session: AsyncSession,
    user_data: UserRegister,
):

    existing_user = await get_user_by_email(session, user_data.email)

    if existing_user:
        raise ValueError("User already exists")

    hashed_password = hash_password(user_data.password)

    user = User(
        email=user_data.email,
        name=user_data.name,
        surname=user_data.surname,
        password=hashed_password,
        role=user_data.role,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(data={"id": str(user.id)})

    return {"user": user, "access_token": token, "token_type": "bearer"}


async def login_user(session: AsyncSession, user_data: UserLogin) -> str:
    user = await get_user_by_email(session, user_data.email)

    if user is None or not verify_password(user_data.password, user.password):
        raise ValueError("Invalid email or password")

    return create_access_token(data={"id": str(user.id)})
