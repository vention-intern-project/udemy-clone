from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_id
from app.db.database import get_db
from app.feature.enrollment.schemas import (
    EnrollmentCreate,
    EnrollmentListResponse,
    EnrollmentResponse,
)
from app.feature.enrollment.service import (
    enroll_in_course,
    get_my_enrollments,
)

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_enrollment_endpoint(
    payload: EnrollmentCreate,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    try:
        enrollment = await enroll_in_course(session, user_id, payload.course_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from None
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except ValueError as e:
        detail = str(e)
        if detail == "Already enrolled in this course":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            ) from None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from None

    return enrollment


@router.get("/my", response_model=EnrollmentListResponse)
async def list_my_enrollments(
    page: int = 1,
    page_size: int = 100,
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await get_my_enrollments(session, user_id, page, page_size)
