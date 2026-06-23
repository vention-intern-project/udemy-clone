from fastapi import APIRouter

from app.api.v1.endpoints.courses import router as courses_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(courses_router)
