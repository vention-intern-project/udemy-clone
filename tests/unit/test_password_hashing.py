from app.core.security import hash_password, verify_password


def test_hash_password():
    password = "secret123"

    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password():
    password = "secret123"

    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
