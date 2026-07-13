from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.cart.repository import (
    add_cart_item,
    clear_cart,
    get_cart_item,
    get_cart_items,
    get_or_create_cart,
    remove_cart_item,
)
from app.feature.cart.schemas import CartItemResponse, CartResponse, CourseSummary, CheckoutResponse
from app.feature.course.repository import get_course_by_id
from app.feature.enrollment.repository import get_enrollment_by_user_and_course
from app.feature.user.models import UserRole
from app.feature.user.repository import get_user_by_id


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


async def add_to_cart(
    session: AsyncSession, user_id: int, course_id: int
) -> CartItemResponse:
    user = await get_user_by_id(session, user_id)
    if user.role != UserRole.STUDENT:
        raise PermissionError("Only students can add courses to cart")

    course = await get_course_by_id(session, course_id)
    if course is None:
        raise LookupError("Course not found")

    if course.published_at is None:
        raise ValueError("Course is not published")

    if course.price == 0:
        raise ValueError("Cannot add free courses to cart")

    cart = await get_or_create_cart(session, user_id)

    existing_item = await get_cart_item(session, cart.id, course_id)
    if existing_item is not None:
        raise ValueError("Course already in cart")

    existing_enrollment = await get_enrollment_by_user_and_course(
        session, user_id, course_id
    )
    if existing_enrollment is not None:
        raise ValueError("Already enrolled in this course")

    cart_item = await add_cart_item(session, cart.id, course_id)

    return CartItemResponse(
        id=cart_item.id,
        course_id=cart_item.course_id,
        added_at=cart_item.added_at,
        course=CourseSummary.model_validate(course),
    )


async def remove_from_cart(session: AsyncSession, user_id: int, course_id: int) -> None:
    cart = await get_or_create_cart(session, user_id)

    existing_item = await get_cart_item(session, cart.id, course_id)
    if existing_item is None:
        raise LookupError("Course not in cart")

    await remove_cart_item(session, cart.id, course_id)


async def clear_cart_items(session: AsyncSession, user_id: int) -> None:
    cart = await get_or_create_cart(session, user_id)
    await clear_cart(session, cart.id)

async def checkout(
        session: AsyncSession,
        user_id: int
) -> CheckoutResponse:

    cart = await get_cart_items(session, user_id)

    if cart is None or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty.",
        )

    enrolled = 0

    try:
        for item in cart.items:

            already_enrolled = await self.repository.enrollment_exists(
                student.id,
                item.course_id,
            )

            if already_enrolled:
                continue

            await self.repository.create_enrollment(
                student.id,
                item.course_id,
            )

            enrolled += 1

        await self.repository.clear_cart(cart)

        await self.session.commit()

    except Exception:
        await self.session.rollback()
        raise

    return CheckoutResponse(
        message="Checkout successful.",
        enrolled_courses=enrolled,
    )