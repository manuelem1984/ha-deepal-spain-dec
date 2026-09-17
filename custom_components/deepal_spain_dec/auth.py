"""Authentication for Deepal Spain DEC."""

from __future__ import annotations

from .models import DeepalSession


class DeepalAuthenticator:
    """Deepal Spain authentication."""

    async def send_sms_code(
        self,
        mobile: str,
    ) -> None:
        """Send SMS verification code."""

    async def send_email_code(
        self,
        email: str,
    ) -> None:
        """Send email verification code."""

    async def login_sms(
        self,
        mobile: str,
        auth_code: str,
    ) -> DeepalSession:
        """Login using SMS code."""
        raise NotImplementedError

    async def login_email(
        self,
        email: str,
        auth_code: str,
    ) -> DeepalSession:
        """Login using email code."""
        raise NotImplementedError

    async def refresh_token(
        self,
        session: DeepalSession,
    ) -> DeepalSession:
        """Refresh session token."""
        raise NotImplementedError
