from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.feature.cart.models import Cart, CartItem


async def get_or_create_cart(session: AsyncSession, student_id: int) -> Cart:
    result = await session.execute(select(Cart).where(Cart.student_id == student_id))
    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(student_id=student_id)
        session.add(cart)
        await session.commit()
        await session.refresh(cart)

    return cart


async def get_cart_items(session: AsyncSession, cart_id: int) -> list[CartItem]:
    result = await session.execute(
        select(CartItem)
        .options(selectinload(CartItem.course))
        .where(CartItem.cart_id == cart_id)
    )
    return list(result.scalars().all())
