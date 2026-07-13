from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.feature.cart.models import Cart, CartItem
from app.feature.enrollment.models import Enrollment


async def get_or_create_cart(session: AsyncSession, student_id: int) -> Cart:
    result = await session.execute(select(Cart).where(Cart.student_id == student_id).options(
                selectinload(Cart.items).selectinload(CartItem.course)
            ))
    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(student_id=student_id)
        session.add(cart)
        await session.commit()
        await session.refresh(cart)

    return cart


async def get_only_cart(session: AsyncSession, student_id: int) -> Cart | None:
    result = await session.execute(select(Cart).where(Cart.student_id == student_id).options(
                selectinload(Cart.items).selectinload(CartItem.course)
            ))
    cart = result.scalar_one_or_none()

    return cart

async def enrollment_exists(
        session: AsyncSession,
        student_id: int,
        course_id: int,
) -> bool:
    stmt = select(Enrollment).where(
        Enrollment.user_id == student_id,
        Enrollment.course_id == course_id,
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


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


async def clear_cart(session: AsyncSession, cart_id: int) -> None:
    result = await session.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    cart_items = result.scalars().all()
    for item in cart_items:
        await session.delete(item)
    await session.commit()
