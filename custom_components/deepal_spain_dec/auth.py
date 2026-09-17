"""Authentication for Deepal Spain DEC."""

from __future__ import annotations

from typing import Any

from .api import DeepalApiClient, DeepalAuthError
from .const import SPAIN_COUNTRY, SPAIN_DIAL_CODE
from .crypto import encrypt_login_value, generate_login_keypair
from .models import DeepalSession


class DeepalAuthenticator:
    """Handle authentication against the Deepal Spain cloud."""

    def __init__(self, api: DeepalApiClient) -> None:
        """Initialize the authenticator."""
        self._api = api
        self._private_key_pem, self._public_key = generate_login_keypair()

    @property
    def private_key_pem(self) -> str:
        """Return the private login key."""
        return self._private_key_pem

    async def send_sms_code(self, mobile: str) -> None:
        """Send an SMS verification code to a Spanish mobile number."""
        await self._api.post(
            "/intl-app-gw/intl-app-auth/api/login/send-auth-code",
            {
                "countryCode": SPAIN_DIAL_CODE,
                "mobile": encrypt_login_value(mobile.strip()),
            },
            include_auth=False,
        )

    async def send_email_code(self, email: str) -> None:
        """Send an email verification code."""
        await self._api.post(
            "/intl-app-gw/intl-app-auth/api/login/email-send-auth-code",
            {
                "type": "0",
                "email": encrypt_login_value(email.strip()),
            },
            include_auth=False,
        )

    async def login_sms(
        self,
        mobile: str,
        auth_code: str,
    ) -> DeepalSession:
        """Complete login using a Spanish mobile number and SMS code."""
        data = await self._api.post(
            "/intl-app-gw/intl-app-auth/api/login/login-by-mobile-code",
            {
                "authCode": auth_code.strip(),
                "countryCode": SPAIN_DIAL_CODE,
                "mobile": encrypt_login_value(mobile.strip()),
                "salesCountry": SPAIN_COUNTRY,
                "pubKey": self._public_key,
            },
            include_auth=False,
        )

        return self._create_session(data)

    async def login_email(
        self,
        email: str,
        auth_code: str,
    ) -> DeepalSession:
        """Complete login using an email address and verification code."""
        data = await self._api.post(
            "/intl-app-gw/intl-app-auth/api/login/email-code-in",
            {
                "authCode": auth_code.strip(),
                "salesCountry": SPAIN_COUNTRY,
                "email": encrypt_login_value(email.strip()),
                "pubKey": self._public_key,
            },
            include_auth=False,
        )

        return self._create_session(data)

    async def refresh_session(
        self,
        session: DeepalSession,
    ) -> DeepalSession:
        """Refresh an authenticated Deepal session."""
        if not session.refresh_token:
            raise DeepalAuthError("No refresh token is available")

        self._api.update_tokens(
            access_token=session.access_token,
            cac_token=session.cac_token,
        )

        data = await self._api.post(
            "/intl-app-gw/intl-app-auth/api/auth/refresh-token",
            {
                "refreshToken": session.refresh_token,
            },
        )

        if not isinstance(data, dict) or not data.get("token"):
            raise DeepalAuthError(
                "Refresh response did not contain an access token"
            )

        refreshed_session = DeepalSession(
            access_token=str(data["token"]),
            refresh_token=(
                data.get("refreshToken")
                or session.refresh_token
            ),
            cac_token=data.get("cacToken") or session.cac_token,
            user_id=session.user_id,
            ca_user_id=session.ca_user_id,
            cac_user_id=session.cac_user_id,
        )

        self._api.update_tokens(
            access_token=refreshed_session.access_token,
            cac_token=refreshed_session.cac_token,
        )

        return refreshed_session

    def _create_session(self, data: Any) -> DeepalSession:
        """Create and register a session from a login response."""
        if not isinstance(data, dict) or not data.get("token"):
            raise DeepalAuthError(
                "Login response did not contain an access token"
            )

        session = DeepalSession(
            access_token=str(data["token"]),
            refresh_token=data.get("refreshToken"),
            cac_token=data.get("cacToken"),
            user_id=data.get("userId"),
            ca_user_id=data.get("caUserId"),
            cac_user_id=data.get("cacUserId"),
        )

        self._api.update_tokens(
            access_token=session.access_token,
            cac_token=session.cac_token,
        )

        return session
