from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.cart.schemas import CartResponse
from app.feature.cart.service import get_cart

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
async def get_cart_endpoint(
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await get_cart(session, user_id)
