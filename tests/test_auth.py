import pytest
from app.auth import get_password_hash, verify_password, create_access_token
from jose import jwt
from app.config import SECRET_KEY, ALGORITHM


def test_password_hashing():
    raw = "super_secure_pass123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_and_decode_jwt_token():
    payload = {"sub": "testuser", "role": "user", "id": 1}
    token = create_access_token(payload)
    assert isinstance(token, str)

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "user"
    assert "exp" in decoded
