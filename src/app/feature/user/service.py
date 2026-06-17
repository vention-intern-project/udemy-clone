from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.security import create_access_token, hash_password, verify_password, generate_reset_token
from app.core.mail import EmailService
from app.feature.user.models import User
from app.feature.user.repository import (get_user_by_email, get_user_by_id, create_reset_token, get_by_reset_token,
                                         mark_reset_token_as_used)
from app.feature.user.schemas import UserLogin, UserRegister, ForgotPasswordRequest, ResetPasswordRequest


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


async def forgot_password(session: AsyncSession, email_data: ForgotPasswordRequest):
    user = await get_user_by_email(
        session,
        email_data.email,
    )

    if user:
        token = generate_reset_token()

        expires_at = (
                datetime.utcnow()
                + timedelta(minutes=15)
        )

        await create_reset_token(session, user.id, token, expires_at)

        await EmailService.send_password_reset_email(
            user.email,
            token,
        )

    return {
        "message": (
            "If the email exists, a reset link has been sent."
        )
    }


async def reset_password(session: AsyncSession, data: ResetPasswordRequest):
    reset_token = await get_by_reset_token(session, data.token)

    if not reset_token or reset_token.used or reset_token.expires_at < datetime.utcnow():
        raise ValueError(
            "Invalid or expired token"
        )

    user = await get_user_by_id(
        session,
        reset_token.user_id,
    )

    if not user:
        raise ValueError("User not found")

    user.password = hash_password(
        data.new_password,
    )

    await mark_reset_token_as_used(session, reset_token)

    await session.commit()

    return {
        "message": "Password successfully updated"
    }
