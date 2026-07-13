from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import carts
from app.db.database import get_db
from app.feature.cart.schemas import CartItemResponse, CartResponse, CourseSummary
from app.main import app


@pytest.fixture
def client():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = lambda: 1
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_get_cart_service(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(carts, "get_cart", mock)
    return mock


@pytest.fixture
def empty_cart_response():
    return CartResponse(
        id=1,
        items=[],
        total_price=0,
        currency="UZS",
        item_count=0,
    )


@pytest.fixture
def cart_with_items_response():
    return CartResponse(
        id=1,
        items=[
            CartItemResponse(
                id=1,
                course_id=1,
                added_at="2026-07-02T12:00:00Z",
                course=CourseSummary(
                    id=1,
                    title="Python 101",
                    price=9.99,
                    currency="USD",
                ),
            ),
            CartItemResponse(
                id=2,
                course_id=2,
                added_at="2026-07-02T12:00:00Z",
                course=CourseSummary(
                    id=2,
                    title="Advanced Django",
                    price=49.99,
                    currency="USD",
                ),
            ),
        ],
        total_price=59.98,
        currency="USD",
        item_count=2,
    )


def test_get_empty_cart(client, mock_get_cart_service, empty_cart_response):
    mock_get_cart_service.return_value = empty_cart_response

    response = client.get(
        "/cart",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["item_count"] == 0
    assert data["total_price"] == "0"


def test_get_cart_with_items(client, mock_get_cart_service, cart_with_items_response):
    mock_get_cart_service.return_value = cart_with_items_response

    response = client.get(
        "/cart",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 2
    assert data["total_price"] == "59.98"
    assert len(data["items"]) == 2
    assert data["items"][0]["course"]["title"] == "Python 101"


def test_get_cart_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.get("/cart")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.fixture
def mock_add_to_cart_service(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(carts, "add_to_cart", mock)
    return mock


@pytest.fixture
def added_cart_item_response():
    return CartItemResponse(
        id=1,
        course_id=1,
        added_at="2026-07-02T12:00:00Z",
        course=CourseSummary(
            id=1,
            title="Python 101",
            price=9.99,
            currency="USD",
        ),
    )


def test_add_course_to_cart(client, mock_add_to_cart_service, added_cart_item_response):
    mock_add_to_cart_service.return_value = added_cart_item_response

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["course_id"] == 1
    assert data["course"]["title"] == "Python 101"


def test_add_nonexistent_course(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = LookupError("Course not found")

    response = client.post(
        "/cart/items",
        json={"course_id": 999},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not found"}


def test_add_unpublished_course(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = ValueError("Course is not published")

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Course is not published"}


def test_add_free_course(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = ValueError("Cannot add free courses to cart")

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot add free courses to cart"}


def test_add_course_already_in_cart(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = ValueError("Course already in cart")

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Course already in cart"}


def test_add_course_already_enrolled(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = ValueError("Already enrolled in this course")

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Already enrolled in this course"}


def test_add_course_non_student(client, mock_add_to_cart_service):
    mock_add_to_cart_service.side_effect = PermissionError(
        "Only students can add courses to cart"
    )

    response = client.post(
        "/cart/items",
        json={"course_id": 1},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Only students can add courses to cart"}


def test_add_course_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.post("/cart/items", json={"course_id": 1})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# --- DELETE /cart/items/{course_id} ---


@pytest.fixture
def mock_remove_from_cart_service(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(carts, "remove_from_cart", mock)
    return mock


def test_remove_course_from_cart(client, mock_remove_from_cart_service):
    mock_remove_from_cart_service.return_value = None

    response = client.delete(
        "/cart/items/1",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204


def test_remove_course_not_in_cart(client, mock_remove_from_cart_service):
    mock_remove_from_cart_service.side_effect = LookupError("Course not in cart")

    response = client.delete(
        "/cart/items/999",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Course not in cart"}


def test_remove_course_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.delete("/cart/items/1")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# --- DELETE /cart ---


@pytest.fixture
def mock_clear_cart_service(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(carts, "clear_cart_items", mock)
    return mock


def test_clear_cart(client, mock_clear_cart_service):
    mock_clear_cart_service.return_value = None

    response = client.delete(
        "/cart",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 204


def test_clear_cart_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.delete("/cart")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
