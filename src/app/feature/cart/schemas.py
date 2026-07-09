from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CheckoutResponse(BaseModel):
    message: str
    enrolled_courses: int


class CartItemAdd(BaseModel):
    course_id: int


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: Decimal
    currency: str


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    added_at: datetime
    course: CourseSummary


class CartResponse(BaseModel):
    id: int
    items: list[CartItemResponse]
    total_price: Decimal
    currency: str
    item_count: int
