from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.feature.user.schemas import (
    RegisterResponse,
    UserLogin,
    UserProfileResponse,
    UserRegister,
)
from app.feature.user.service import get_user_profile, login_user, register_user

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def _extract_user_id(payload: dict) -> int:
    value = payload.get("id")
    if value is not None:
        return int(value)
    raise ValueError("Token payload does not contain a user identifier")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


@router.get("/me", response_model=UserProfileResponse)
async def read_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
):
    # Checking is existing bearer
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    # Decoding and checking JWT
    try:
        payload = decode_token(credentials.credentials)
        user_id = _extract_user_id(payload)
        print(user_id)
    except Exception:
        raise _unauthorized() from None

    # Getting user by passing db session and user_id
    user = await get_user_profile(session, user_id)

    if user is None:
        raise _unauthorized()

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
