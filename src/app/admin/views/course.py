from sqladmin import ModelView

from app.feature.course.models import Course


class CourseAdmin(ModelView, model=Course):
    name = "Course"
    name_plural = "Courses"
    can_delete = True
    can_edit = True
    can_create = True

    column_list = [
        Course.id,
        Course.title,
        Course.description,
        Course.instructor_id,
        Course.price,
        Course.currency,
        Course.published_at,
        Course.created_at,
        Course.updated_at,
    ]

    column_searchable_list = [
        Course.title,
        Course.description,
    ]

    column_sortable_list = [
        Course.title,
        Course.created_at,
        Course.price,
    ]

    form_columns = [
        Course.title,
        Course.description,
        Course.price,
        Course.currency,
    ]
