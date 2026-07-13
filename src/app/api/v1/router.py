from fastapi import APIRouter

from app.api.v1.endpoints.carts import router as carts_router
from app.api.v1.endpoints.courses import router as courses_router
from app.api.v1.endpoints.enrollments import router as enrollments_router
from app.api.v1.endpoints.lessons import router as lessons_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(courses_router)
api_router.include_router(enrollments_router)
api_router.include_router(lessons_router)
api_router.include_router(carts_router)
