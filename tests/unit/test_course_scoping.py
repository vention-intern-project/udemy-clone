import asyncio
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.dialects import postgresql

from app.feature.course import service as course_service
from app.feature.course.repository import get_all_courses
from app.feature.course.schemas import CourseFilters
from app.feature.course.service import get_courses_list


def run(coro):
    return asyncio.run(coro)


def make_session() -> AsyncMock:
    """AsyncMock chains async by default; Result.scalars() is sync in SQLAlchemy."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    session.execute.return_value.scalars.return_value.all.return_value = []
    return session


def compile_statement(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def page_sql(session) -> str:
    return compile_statement(session.execute.await_args.args[0])


def count_sql(session) -> str:
    return compile_statement(session.scalar.await_args.args[0])


def test_owner_filter_reaches_the_page_query():
    session = make_session()

    run(
        get_all_courses(
            session,
            page=1,
            page_size=20,
            filters=CourseFilters(),
            instructor_id=7,
        )
    )

    assert "courses.instructor_id = 7" in page_sql(session)


def test_owner_filter_reaches_the_count_query():
    """A scoped page with an unscoped total would leak other instructors' counts."""
    session = make_session()

    run(
        get_all_courses(
            session,
            page=1,
            page_size=20,
            filters=CourseFilters(),
            instructor_id=7,
        )
    )

    assert "courses.instructor_id = 7" in count_sql(session)


def test_public_listing_stays_unscoped():
    session = make_session()

    run(get_all_courses(session, page=1, page_size=20, filters=CourseFilters()))

    assert "courses.instructor_id =" not in page_sql(session)


def test_service_forwards_instructor_id_to_repository(monkeypatch):
    """The owner filter must be applied in SQL, not by filtering rows in Python."""
    get_all_mock = AsyncMock(return_value=([], 0))
    monkeypatch.setattr(course_service, "get_all_courses", get_all_mock)
    monkeypatch.setattr(course_service, "get_user_by_id", AsyncMock(return_value=None))

    run(
        get_courses_list(
            AsyncMock(),
            page=1,
            page_size=20,
            filters=CourseFilters(),
            viewer_id=7,
            instructor_id=7,
        )
    )

    assert get_all_mock.await_args.kwargs["instructor_id"] == 7
