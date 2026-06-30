from datetime import UTC, datetime, timedelta

import pytest
from jose import JWTError, jwt

from app.core import security


@pytest.fixture(autouse=True)
def security_settings(monkeypatch):
    monkeypatch.setattr(security.settings, "SECRET_KEY", "test-secret-key")
    monkeypatch.setattr(security.settings, "ALGORITHM", "HS256")
    monkeypatch.setattr(security.settings, "ACCESS_TOKEN_EXPIRE_HOURS", 2)


def test_create_access_token_sets_type_and_expiry():
    token = security.create_access_token({"id": "42"})

    decoded = jwt.decode(
        token, "test-secret-key", algorithms=["HS256"], options={"verify_exp": False}
    )
    assert decoded["type"] == "access"
    assert decoded["id"] == "42"
    assert "exp" in decoded


def test_create_access_token_with_custom_expiry():
    token = security.create_access_token({}, expires_delta=timedelta(minutes=15))

    decoded = jwt.decode(
        token, "test-secret-key", algorithms=["HS256"], options={"verify_exp": False}
    )
    assert decoded["type"] == "access"


def test_decode_token_returns_valid_payload():
    token = security.create_access_token({"id": "42"})

    decoded = security.decode_token(token)

    assert decoded["type"] == "access"
    assert decoded["id"] == "42"


def test_decode_token_rejects_wrong_type():
    token = jwt.encode(
        {
            "sub": "123",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        "test-secret-key",
        algorithm="HS256",
    )

    with pytest.raises(JWTError, match="Invalid token type"):
        security.decode_token(token)


def test_decode_token_rejects_expired_token():
    token = jwt.encode(
        {"sub": "123", "type": "access", "exp": datetime.now(UTC) - timedelta(hours=1)},
        "test-secret-key",
        algorithm="HS256",
    )

    with pytest.raises(JWTError):
        security.decode_token(token)


def test_decode_token_rejects_wrong_secret():
    token = jwt.encode(
        {"sub": "123", "type": "access", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "wrong-secret",
        algorithm="HS256",
    )

    with pytest.raises(JWTError):
        security.decode_token(token)
