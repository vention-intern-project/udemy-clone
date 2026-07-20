from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_current_user_id
from app.api.v1.endpoints import payments
from app.db.database import get_db
from app.feature.payment.schemas import PaymentCompleteResponse
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
def mock_complete_payment_service(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(payments, "complete_payment", mock)
    return mock


@pytest.fixture
def successful_payment_response():
    return PaymentCompleteResponse(
        enrollment_id=1,
        status="active",
        message="Payment successful.",
    )


@pytest.fixture
def failed_payment_response():
    return PaymentCompleteResponse(
        enrollment_id=1,
        status="cancelled",
        message="Payment failed.",
    )


# --- POST /payments/complete ---


def test_payment_success(
    client, mock_complete_payment_service, successful_payment_response
):
    mock_complete_payment_service.return_value = successful_payment_response

    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 1, "status": "success"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["enrollment_id"] == 1
    assert data["status"] == "active"
    assert data["message"] == "Payment successful."


def test_payment_failed(client, mock_complete_payment_service, failed_payment_response):
    mock_complete_payment_service.return_value = failed_payment_response

    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 1, "status": "failed"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["enrollment_id"] == 1
    assert data["status"] == "cancelled"
    assert data["message"] == "Payment failed."


def test_payment_enrollment_not_found(client, mock_complete_payment_service):
    mock_complete_payment_service.side_effect = LookupError("Enrollment not found")

    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 999, "status": "success"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Enrollment not found"}


def test_payment_not_your_enrollment(client, mock_complete_payment_service):
    mock_complete_payment_service.side_effect = PermissionError(
        "You do not have access to this enrollment"
    )

    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 1, "status": "success"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have access to this enrollment"}


def test_payment_enrollment_not_awaiting(client, mock_complete_payment_service):
    mock_complete_payment_service.side_effect = ValueError(
        "Enrollment is not awaiting payment"
    )

    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 1, "status": "success"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Enrollment is not awaiting payment"}


def test_payment_requires_auth():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user_id, None)
    with TestClient(app) as c:
        response = c.post(
            "/payments/complete",
            json={"enrollment_id": 1, "status": "success"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_payment_invalid_status(client):
    response = client.post(
        "/payments/complete",
        json={"enrollment_id": 1, "status": "invalid"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422


def test_payment_missing_fields(client):
    response = client.post(
        "/payments/complete",
        json={},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 422
