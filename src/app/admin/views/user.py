from sqladmin import ModelView

from app.core.security import hash_password
from app.feature.user.models import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.name,
        User.surname,
        User.role,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.name, User.surname]
    column_sortable_list = [User.id, User.email, User.created_at]
    column_details_list = [
        User.id,
        User.email,
        User.name,
        User.surname,
        User.role,
        User.birthday,
        User.phone_number,
        User.created_at,
    ]
    form_excluded_columns = []
    can_delete = True
    can_edit = True
    can_create = True
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    form_args = {
        "password": {"label": "Password", "description": "Plain text - will be hashed"},
    }

    async def insert_model(self, request, data):
        if "password" in data and data["password"]:
            data["password"] = hash_password(data["password"])
        else:
            data["password"] = hash_password("changeme123")
        return await super().insert_model(request, data)
