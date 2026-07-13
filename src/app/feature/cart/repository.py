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


async def get_cart_item(
    session: AsyncSession, cart_id: int, course_id: int
) -> CartItem | None:
    result = await session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.course_id == course_id,
        )
    )
    return result.scalar_one_or_none()


async def add_cart_item(
    session: AsyncSession, cart_id: int, course_id: int
) -> CartItem:
    cart_item = CartItem(cart_id=cart_id, course_id=course_id)
    session.add(cart_item)
    await session.commit()
    await session.refresh(cart_item)
    return cart_item


async def remove_cart_item(session: AsyncSession, cart_id: int, course_id: int) -> None:
    result = await session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.course_id == course_id,
        )
    )
    cart_item = result.scalar_one_or_none()
    if cart_item:
        await session.delete(cart_item)
        await session.commit()
