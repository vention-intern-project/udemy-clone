from sqlalchemy.ext.asyncio import AsyncSession

from app.feature.enrollment.models import EnrollmentStatus
from app.feature.enrollment.repository import (
    get_enrollment_by_id,
    update_enrollment_status,
)
from app.feature.payment.schemas import PaymentCompleteResponse


async def complete_payment(
    session: AsyncSession,
    user_id: int,
    enrollment_id: int,
    payment_status: str,
) -> PaymentCompleteResponse:
    enrollment = await get_enrollment_by_id(session, enrollment_id)

    if enrollment is None:
        raise LookupError("Enrollment not found")

    if enrollment.user_id != user_id:
        raise PermissionError("You do not have access to this enrollment")

    if enrollment.status != EnrollmentStatus.PENDING_PAYMENT:
        raise ValueError("Enrollment is not awaiting payment")

    if payment_status == "success":
        new_status = EnrollmentStatus.ACTIVE
        message = "Payment successful."
    else:
        new_status = EnrollmentStatus.CANCELLED
        message = "Payment failed."

    await update_enrollment_status(session, enrollment_id, new_status)

    return PaymentCompleteResponse(
        enrollment_id=enrollment_id,
        status=new_status.value,
        message=message,
    )
