from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.cart.repository import get_cart_items, get_or_create_cart
from app.feature.cart.schemas import CartItemResponse, CartResponse, CourseSummary


async def get_cart(session: AsyncSession, user_id: int) -> CartResponse:
    cart = await get_or_create_cart(session, user_id)
    items = await get_cart_items(session, cart.id)

    cart_items = []
    total_price = Decimal("0")
    for item in items:
        if item.course is None:
            continue

        cart_items.append(
            CartItemResponse(
                id=item.id,
                course_id=item.course_id,
                added_at=item.added_at,
                course=CourseSummary.model_validate(item.course),
            )
        )
        total_price += item.course.price

    currency = items[0].course.currency if items else "UZS"

    return CartResponse(
        id=cart.id,
        items=cart_items,
        total_price=total_price,
        currency=currency,
        item_count=len(items),
    )
