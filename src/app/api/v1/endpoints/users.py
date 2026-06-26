from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.user.schemas import (
    ForgotPasswordRequest,
    RegisterResponse,
    ResetPasswordRequest,
    UserLogin,
    UserProfileResponse,
    UserRegister,
)
from app.feature.user.service import (
    forgot_password,
    get_user_profile,
    login_user,
    register_user,
    reset_password,
)

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def read_current_user(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_profile(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user


@router.post("/signup", response_model=RegisterResponse)
async def register(
    user_data: UserRegister,
    session: AsyncSession = Depends(get_db),
):
    try:
        user = await register_user(session, user_data)
        return user

    except ValueError as err:
        raise HTTPException(status_code=400, detail="User already exists") from err


@router.post("/login")
async def login(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_db),
):
    try:
        token = await login_user(session, user_data)
        return {"access_token": token}
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid email or password"
        ) from None


@router.post("/forgot-password")
async def forgot_user_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    await forgot_password(session, request)

    return {"message": "If account exists, reset email sent"}


@router.post("/reset-password")
async def reset_user_password(
    request: ResetPasswordRequest, session: AsyncSession = Depends(get_db)
):
    try:
        await reset_password(session, request)

        return {"message": "Password reset successful"}
    except ValueError as err:
        raise HTTPException(
            status_code=400, detail="Token is expired or user not found"
        ) from err
