"""Authentication helpers for the local web application."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.models import AuthSession, UserAccount


SESSION_TTL_DAYS = 30
PASSWORD_ITERATIONS = 310_000


@dataclass(frozen=True)
class AuthResult:
    """Successful authentication response."""

    user: UserAccount
    access_token: str
    token_type: str = "bearer"


class AuthService:
    """Handle user registration and bearer-token sessions."""

    def register_user(self, session: Session, *, name: str, email: str, password: str) -> AuthResult:
        """Create a user account and issue a fresh session token."""

        normalized_email = email.strip().lower()
        existing = self.get_user_by_email(session, normalized_email)
        if existing is not None:
            raise ValueError("Email already exists")

        user = UserAccount(
            name=name.strip(),
            email=normalized_email,
            password_hash=self._hash_password(password),
            is_active=True,
        )
        session.add(user)
        session.flush()
        token = self._create_session(session, user)
        return AuthResult(user=user, access_token=token)

    def authenticate_user(self, session: Session, *, email: str, password: str) -> AuthResult:
        """Validate credentials and issue a fresh session token."""

        user = self.get_user_by_email(session, email.strip().lower())
        if user is None or not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        token = self._create_session(session, user)
        return AuthResult(user=user, access_token=token)

    def get_user_by_email(self, session: Session, email: str) -> UserAccount | None:
        """Look up a user by email."""

        statement = select(UserAccount).where(UserAccount.email == email.strip().lower())
        return session.scalar(statement)

    def get_current_user(self, session: Session, token: str) -> UserAccount | None:
        """Resolve the bearer token to an active user."""

        token_hash = self._hash_token(token)
        statement = (
            select(AuthSession)
            .where(AuthSession.token_hash == token_hash)
            .limit(1)
        )
        auth_session = session.scalar(statement)
        if auth_session is None:
            return None
        if auth_session.revoked_at is not None or auth_session.expires_at <= datetime.utcnow():
            return None
        user = session.get(UserAccount, auth_session.user_id)
        if user is None or not user.is_active:
            return None
        auth_session.last_used_at = datetime.utcnow()
        session.flush()
        return user

    def revoke_token(self, session: Session, token: str) -> None:
        """Invalidate a bearer token."""

        token_hash = self._hash_token(token)
        statement = select(AuthSession).where(AuthSession.token_hash == token_hash).limit(1)
        auth_session = session.scalar(statement)
        if auth_session is None:
            return
        auth_session.revoked_at = datetime.utcnow()
        session.flush()

    def serialize_user(self, user: UserAccount) -> dict[str, object]:
        """Return the safe user payload exposed to the frontend."""

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
        }

    def _create_session(self, session: Session, user: UserAccount) -> str:
        """Persist a new session row and return the raw bearer token."""

        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        auth_session = AuthSession(
            user_id=user.id,
            token_hash=self._hash_token(token),
            expires_at=now + timedelta(days=SESSION_TTL_DAYS),
            revoked_at=None,
            last_used_at=now,
        )
        session.add(auth_session)
        session.flush()
        return token

    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2."""

        salt = secrets.token_bytes(16)
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PASSWORD_ITERATIONS,
        )
        return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${derived_key.hex()}"

    def verify_password(self, password: str, encoded_hash: str) -> bool:
        """Verify a password against a stored PBKDF2 hash."""

        try:
            algorithm, iterations, salt_hex, hash_hex = encoded_hash.split("$", 3)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(derived_key.hex(), hash_hex)

    def _hash_token(self, token: str) -> str:
        """Hash a bearer token before storing or matching it."""

        return hashlib.sha256(token.encode("utf-8")).hexdigest()
