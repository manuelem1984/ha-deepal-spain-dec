"""Error classification for the Deepal Spain DEC HTTP API.

Kept free of aiohttp and Home Assistant imports so the auth-error
detection logic (is_auth_error) can be unit tested on its own, without
either installed.
"""

from __future__ import annotations


class DeepalApiError(Exception):
    """Base exception for Deepal API errors."""


class DeepalAuthError(DeepalApiError):
    """Raised when the Deepal session token is missing, invalid or expired.

    Deepal only allows one active session per account: signing in again
    from the official app invalidates the token Home Assistant is using
    (see README, "Avisos Importantes"). Raising this (rather than the
    generic DeepalApiError) is what lets the coordinator trigger Home
    Assistant's reauthentication flow instead of just retrying forever.
    """


class DeepalRateLimitError(DeepalApiError):
    """Raised when Deepal limits verification-code requests."""


# Deepal error codes observed in the wild that mean the session token is
# no longer valid, beyond the generic "AUTH" / "401" patterns already
# checked in is_auth_error().
KNOWN_AUTH_ERROR_CODES = frozenset(
    {
        "APP_1_1_02_004",
        "APP_1_1_02_005",
    }
)


def is_auth_error(code: str, message: str) -> bool:
    """Return True if a Deepal API error means the session must be renewed.

    Covers both structured error codes (e.g. "APP_1_1_02_004") and
    free-text messages Deepal sometimes returns instead, such as the
    real-world "APIGW_-1_7_01_004 invalided token" (note: "invalided",
    not "invalid" — that's how Deepal's backend actually spells it).
    """
    normalized_code = code.upper()
    normalized_message = message.lower()

    if "AUTH" in normalized_code:
        return True

    if normalized_code.startswith("401"):
        return True

    if normalized_code in KNOWN_AUTH_ERROR_CODES:
        return True

    if "token" in normalized_message and (
        "invalid" in normalized_message
        or "expired" in normalized_message
        or "caduc" in normalized_message
    ):
        return True

    return False
