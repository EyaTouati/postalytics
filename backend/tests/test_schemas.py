import pytest
from pydantic import ValidationError

from app.schemas.schemas import LoginRequest


def test_login_request_accepts_username_and_password():
    payload = LoginRequest(username="agent_tunis", password="secret")

    assert payload.username == "agent_tunis"
    assert payload.password == "secret"


def test_login_request_requires_credentials():
    with pytest.raises(ValidationError):
        LoginRequest(username="admin")
