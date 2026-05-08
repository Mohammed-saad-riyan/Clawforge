"""Supabase authentication for ClawForge.

Provides user authentication using Supabase Auth:
- Email/password signup and login
- OAuth providers (Google, GitHub)
- Session management
- Password reset
"""

from dataclasses import dataclass
from typing import Any

from clawforge.supabase.client import get_supabase_client


@dataclass
class AuthUser:
    """Authenticated user information."""

    id: str
    email: str
    email_confirmed: bool = False
    created_at: str = ""
    updated_at: str = ""
    user_metadata: dict = None

    def __post_init__(self):
        if self.user_metadata is None:
            self.user_metadata = {}


@dataclass
class AuthSession:
    """Authentication session."""

    access_token: str
    refresh_token: str
    expires_in: int
    expires_at: int
    token_type: str = "bearer"
    user: AuthUser | None = None


class SupabaseAuth:
    """Supabase authentication client."""

    def __init__(self):
        self.client = get_supabase_client()

    async def sign_up(
        self,
        email: str,
        password: str,
        user_metadata: dict | None = None,
    ) -> tuple[AuthUser | None, str | None]:
        """Sign up a new user with email and password.

        Args:
            email: User's email
            password: User's password (min 6 characters)
            user_metadata: Optional metadata to store with user

        Returns:
            Tuple of (user, error_message)
        """
        try:
            options = {}
            if user_metadata:
                options["data"] = user_metadata

            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": options if options else None,
            })

            if response.user:
                user = AuthUser(
                    id=response.user.id,
                    email=response.user.email or "",
                    email_confirmed=response.user.email_confirmed_at is not None,
                    created_at=str(response.user.created_at) if response.user.created_at else "",
                    user_metadata=response.user.user_metadata or {},
                )
                return user, None

            return None, "Sign up failed"

        except Exception as e:
            return None, str(e)

    async def sign_in(
        self,
        email: str,
        password: str,
    ) -> tuple[AuthSession | None, str | None]:
        """Sign in with email and password.

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (session, error_message)
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            if response.session:
                user = None
                if response.user:
                    user = AuthUser(
                        id=response.user.id,
                        email=response.user.email or "",
                        email_confirmed=response.user.email_confirmed_at is not None,
                        created_at=str(response.user.created_at) if response.user.created_at else "",
                        user_metadata=response.user.user_metadata or {},
                    )

                session = AuthSession(
                    access_token=response.session.access_token,
                    refresh_token=response.session.refresh_token,
                    expires_in=response.session.expires_in or 3600,
                    expires_at=response.session.expires_at or 0,
                    user=user,
                )
                return session, None

            return None, "Sign in failed"

        except Exception as e:
            return None, str(e)

    async def sign_out(self) -> tuple[bool, str | None]:
        """Sign out the current user.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.client.auth.sign_out()
            return True, None
        except Exception as e:
            return False, str(e)

    async def get_user(self, access_token: str) -> tuple[AuthUser | None, str | None]:
        """Get user from access token.

        Args:
            access_token: JWT access token

        Returns:
            Tuple of (user, error_message)
        """
        try:
            response = self.client.auth.get_user(access_token)

            if response.user:
                user = AuthUser(
                    id=response.user.id,
                    email=response.user.email or "",
                    email_confirmed=response.user.email_confirmed_at is not None,
                    created_at=str(response.user.created_at) if response.user.created_at else "",
                    user_metadata=response.user.user_metadata or {},
                )
                return user, None

            return None, "User not found"

        except Exception as e:
            return None, str(e)

    async def refresh_session(
        self,
        refresh_token: str,
    ) -> tuple[AuthSession | None, str | None]:
        """Refresh an expired session.

        Args:
            refresh_token: Refresh token from previous session

        Returns:
            Tuple of (new_session, error_message)
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                user = None
                if response.user:
                    user = AuthUser(
                        id=response.user.id,
                        email=response.user.email or "",
                        email_confirmed=response.user.email_confirmed_at is not None,
                        user_metadata=response.user.user_metadata or {},
                    )

                session = AuthSession(
                    access_token=response.session.access_token,
                    refresh_token=response.session.refresh_token,
                    expires_in=response.session.expires_in or 3600,
                    expires_at=response.session.expires_at or 0,
                    user=user,
                )
                return session, None

            return None, "Session refresh failed"

        except Exception as e:
            return None, str(e)

    async def reset_password(self, email: str) -> tuple[bool, str | None]:
        """Send password reset email.

        Args:
            email: User's email

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.client.auth.reset_password_for_email(email)
            return True, None
        except Exception as e:
            return False, str(e)

    async def update_password(
        self,
        access_token: str,
        new_password: str,
    ) -> tuple[bool, str | None]:
        """Update user's password.

        Args:
            access_token: Current access token
            new_password: New password

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.client.auth.update_user({
                "password": new_password,
            })
            return True, None
        except Exception as e:
            return False, str(e)


# Global auth instance
_auth_client: SupabaseAuth | None = None


def get_auth_client() -> SupabaseAuth:
    """Get the global auth client instance."""
    global _auth_client
    if _auth_client is None:
        _auth_client = SupabaseAuth()
    return _auth_client
