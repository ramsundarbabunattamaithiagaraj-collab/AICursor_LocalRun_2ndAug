from __future__ import annotations

import pytest

from app.core.security import decode_access_token
from app.schemas.auth import UserLogin, UserRegister
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError, DuplicateResourceError


class TestRegistration:
    def test_register_success(self, db_session):
        user = AuthService(db_session).register(
            UserRegister(username="jdoe", email="jdoe@example.com", password="StrongPass1")
        )
        assert user.id is not None
        assert user.hashed_password != "StrongPass1"

    def test_register_duplicate_username_raises(self, db_session):
        service = AuthService(db_session)
        service.register(UserRegister(username="jdoe", email="a@example.com", password="StrongPass1"))
        with pytest.raises(DuplicateResourceError):
            service.register(UserRegister(username="jdoe", email="b@example.com", password="StrongPass1"))

    def test_register_duplicate_email_raises(self, db_session):
        service = AuthService(db_session)
        service.register(UserRegister(username="user1", email="dup@example.com", password="StrongPass1"))
        with pytest.raises(DuplicateResourceError):
            service.register(UserRegister(username="user2", email="dup@example.com", password="StrongPass1"))


class TestAuthentication:
    def test_login_success_returns_valid_token(self, db_session):
        service = AuthService(db_session)
        service.register(UserRegister(username="jdoe", email="jdoe@example.com", password="StrongPass1"))

        token_response = service.authenticate(UserLogin(username="jdoe", password="StrongPass1"))

        assert token_response.access_token
        payload = decode_access_token(token_response.access_token)
        assert payload is not None
        assert payload["sub"] == str(token_response.user.id)

    def test_login_wrong_password_raises(self, db_session):
        service = AuthService(db_session)
        service.register(UserRegister(username="jdoe", email="jdoe@example.com", password="StrongPass1"))
        with pytest.raises(AuthenticationError):
            service.authenticate(UserLogin(username="jdoe", password="WrongPassword"))

    def test_login_unknown_user_raises(self, db_session):
        with pytest.raises(AuthenticationError):
            AuthService(db_session).authenticate(UserLogin(username="ghost", password="whatever"))
