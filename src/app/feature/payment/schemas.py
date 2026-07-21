from typing import Literal

from pydantic import BaseModel


class PaymentCompleteRequest(BaseModel):
    enrollment_id: int
    status: Literal["success", "failed"]


class PaymentCompleteResponse(BaseModel):
    enrollment_id: int
    status: str
    message: str
