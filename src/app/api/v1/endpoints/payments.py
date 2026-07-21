from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.payment.schemas import PaymentCompleteRequest, PaymentCompleteResponse
from app.feature.payment.service import complete_payment

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/complete", response_model=PaymentCompleteResponse)
async def mock_payment_complete(
    request: PaymentCompleteRequest,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> PaymentCompleteResponse:
    try:
        return await complete_payment(
            session, user_id, request.enrollment_id, request.status
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
