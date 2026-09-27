from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_verifies_and_is_not_plaintext():
    password = "TestPassword-2026!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip_and_expiration_claim():
    token = create_access_token(
        {"sub": "42", "role": "responsable"},
        expires_delta=timedelta(minutes=5),
    )
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "responsable"
    assert "exp" in payload
