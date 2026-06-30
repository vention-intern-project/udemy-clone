from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import users
from app.db.database import get_db
from app.main import app


@pytest.fixture
def client():
    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_service(monkeypatch):
    register_mock = AsyncMock()
    forgot_mock = AsyncMock()
    reset_mock = AsyncMock()

    monkeypatch.setattr(users, "register_user", register_mock)
    monkeypatch.setattr(users, "forgot_password", forgot_mock)
    monkeypatch.setattr(users, "reset_password", reset_mock)

    return register_mock, forgot_mock, reset_mock


def test_register_success(client, mock_auth_service):
    register, _, _ = mock_auth_service

    register.return_value = {
        "user": {
            "id": 1,
            "email": "john@example.com",
        },
        "access_token": "fake-access-token",
        "token_type": "bearer",
    }

    response = client.post(
        "/signup",
        json={
            "email": "john@example.com",
            "name": "John",
            "surname": "Doe",
            "password": "Password123!",
            "role": "student",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "john@example.com"


def test_register_duplicate_email(client, mock_auth_service):
    register, _, _ = mock_auth_service

    register.side_effect = ValueError("Email already exists")

    response = client.post(
        "/signup",
        json={
            "email": "john@example.com",
            "name": "John",
            "surname": "Doe",
            "password": "Password123!",
            "role": "student",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


def test_register_invalid_email(client):
    response = client.post(
        "/signup",
        json={
            "email": "not-an-email",
            "name": "John",
            "surname": "Doe",
            "password": "Password123!",
            "role": "student",
        },
    )

    assert response.status_code == 400


def test_register_missing_password(client):
    response = client.post(
        "/signup",
        json={
            "email": "john@example.com",
            "name": "John",
            "surname": "Doe",
            "role": "student",
        },
    )

    assert response.status_code == 422


def test_forgot_password_success(client, mock_auth_service):
    _, forgot, _ = mock_auth_service

    forgot.return_value = {"message": "If account exists, reset email sent"}

    response = client.post("/forgot-password", json={"email": "john@example.com"})

    assert response.status_code == 200
    assert response.json()["message"] == "If account exists, reset email sent"


def test_forgot_password_invalid_email(client):
    response = client.post("/forgot-password", json={"email": "abc"})

    assert response.status_code == 422


def test_reset_password_success(client, mock_auth_service):
    _, _, reset = mock_auth_service

    reset.return_value = {"message": "Password reset successful"}

    response = client.post(
        "/reset-password",
        json={"token": "valid-token", "new_password": "NewPassword123!"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"


def test_reset_password_invalid_token(client, mock_auth_service):
    _, _, reset = mock_auth_service

    reset.side_effect = ValueError("Token is expired or user not found")

    response = client.post(
        "/reset-password",
        json={"token": "bad-token", "new_password": "NewPassword123!"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Token is expired or user not found"


def test_reset_password_expired_token(client, mock_auth_service):
    _, _, reset = mock_auth_service

    reset.side_effect = ValueError("Token is expired or user not found")

    response = client.post(
        "/reset-password",
        json={"token": "expired-token", "new_password": "NewPassword123!"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Token is expired or user not found"


def test_reset_password_missing_token(client):
    response = client.post("/reset-password", json={"new_password": "NewPassword123!"})

    assert response.status_code == 422


@pytest.fixture
def mock_login_service(monkeypatch):
    login_mock = AsyncMock()
    monkeypatch.setattr(users, "login_user", login_mock)
    return login_mock


def test_login_success(client, mock_login_service):
    mock_login_service.return_value = "fake-jwt-token"

    response = client.post(
        "/login",
        json={"email": "john@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake-jwt-token"


def test_login_wrong_password(client, mock_login_service):
    mock_login_service.side_effect = ValueError("Invalid credentials")

    response = client.post(
        "/login",
        json={"email": "john@example.com", "password": "WrongPassword!"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_email(client, mock_login_service):
    mock_login_service.side_effect = ValueError("Invalid credentials")

    response = client.post(
        "/login",
        json={"email": "unknown@example.com", "password": "Password123!"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"


def test_login_missing_fields(client):
    response = client.post("/login", json={})

    assert response.status_code == 422


def test_login_invalid_email_format(client):
    response = client.post(
        "/login",
        json={"email": "not-an-email", "password": "Password123!"},
    )

    assert response.status_code == 422
