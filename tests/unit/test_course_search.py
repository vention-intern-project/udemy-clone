from sqlalchemy.dialects import postgresql

from app.feature.course.repository import build_search_condition


def compile_condition(search_query: str) -> str:
    return str(
        build_search_condition(search_query).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def test_search_matches_full_name():
    sql = compile_condition("Samira Karimova")

    assert "concat(users.name, ' ', users.surname) ILIKE" in sql


def test_search_matches_reversed_full_name():
    sql = compile_condition("Karimova Samira")

    assert "concat(users.surname, ' ', users.name) ILIKE" in sql


def test_search_still_matches_course_text():
    sql = compile_condition("python")

    assert "courses.title ILIKE" in sql
    assert "courses.description ILIKE" in sql


def test_search_normalizes_surrounding_and_repeated_whitespace():
    sql = compile_condition("  Samira   Karimova ")

    # `%%` is the compiler escaping `%` for the pyformat paramstyle.
    assert "'%%Samira Karimova%%'" in sql
    assert "Samira   Karimova" not in sql
