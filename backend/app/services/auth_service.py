"""Authentication service: registration, login, JWT issuance."""
from __future__ import annotations

from app.core.logging_config import get_logger
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
from app.utils.exceptions import AuthenticationError, DuplicateResourceError

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.settings = get_settings()

    def register(self, payload: UserRegister) -> User:
        if self.repo.get_by_username(payload.username):
            raise DuplicateResourceError("User", "username", payload.username)
        if self.repo.get_by_email(payload.email):
            raise DuplicateResourceError("User", "email", payload.email)

        user = User(
            username=payload.username,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        created = self.repo.add(user)
        logger.info("User registered: username=%s role=%s", created.username, created.role.value)
        return created

    def authenticate(self, payload: UserLogin) -> TokenResponse:
        user = self.repo.get_by_username(payload.username)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password.")
        if not user.is_active:
            raise AuthenticationError("User account is disabled.")

        token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
        logger.info("User authenticated: username=%s", user.username)
        return TokenResponse(
            access_token=token,
            expires_in_minutes=self.settings.auth.access_token_expire_minutes,
            user=user,
        )
