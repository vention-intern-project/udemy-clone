from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.security import verify_password
from app.db.database import SessionLocal
from app.feature.user.models import User, UserRole


class SuperAdminAuth:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.middlewares = [
            Middleware(SessionMiddleware, secret_key=secret_key),
        ]

    async def login(self, request: Request) -> Response | bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user:
            return False

        if user.role != UserRole.ADMIN:
            return False

        if not verify_password(password, user.password):
            return False

        request.session["user_id"] = user.id
        return True

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse("/admin/login", status_code=302)
        return True


def create_admin(app):
    from sqladmin import Admin

    from app.db.database import engine

    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=SuperAdminAuth(secret_key=settings.SECRET_KEY),
        title="Admin Panel",
        base_url="/admin",
    )

    from app.admin.views.user import UserAdmin
    from app.admin.views.course import CourseAdmin

    admin.add_view(UserAdmin)
    admin.add_view(CourseAdmin)

    return admin
