"""Unit tests for api_errors.is_auth_error.

Pure-function tests: no network, no aiohttp, no Home Assistant required.
"""

from __future__ import annotations

import pytest

from custom_components.deepal_spain_dec import api_errors


@pytest.mark.parametrize(
    ("code", "message"),
    [
        # The real-world case that motivated this: seen live on 2026-09-18
        # ("Unable to update Deepal telemetry: Deepal API error for
        # /user-apigw/vot-connect-conf-center/api/device/getConnConf:
        # APIGW_-1_7_01_004 invalided token"). Before this fix it was
        # misclassified as a generic DeepalApiError, so Home Assistant
        # just retried forever instead of prompting to reauthenticate.
        ("APIGW_-1_7_01_004", "invalided token"),
        # Generic patterns already handled before this fix.
        ("APP_AUTH_FAILED", "session expired"),
        ("401_UNAUTHORIZED", "unauthorized"),
        ("APP_1_1_02_004", "some message"),
        ("APP_1_1_02_005", "some message"),
        # Added after cross-checking with another open-source Deepal
        # integration (ha-deepal-alternative), which documents these
        # as additional gateway kick-out codes; not yet each
        # individually observed by us.
        ("APP_1_1_02_003", "some message"),
        ("APP_1_1_02_006", "some message"),
        ("CAC_1_1_01_045", "some message"),
        # Case-insensitivity and alternate wording.
        ("app_auth_failed", "SESSION EXPIRED"),
        ("SYS_1_1_01_099", "the token has expired, please sign in again"),
        ("SYS_1_1_01_099", "token caducado"),
    ],
)
def test_is_auth_error_true_cases(code, message):
    assert api_errors.is_auth_error(code, message) is True


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("CAC_1_1_01_033", "too many verification codes requested"),
        ("SYS_1_1_01_099", "internal server error"),
        ("SYS_1_1_01_002", "vehicle not found"),
        ("", ""),
        ("400_BAD_REQUEST", "malformed request"),  # "400", not "401"
    ],
)
def test_is_auth_error_false_cases(code, message):
    assert api_errors.is_auth_error(code, message) is False


def test_deepal_command_not_ready_is_a_deepal_api_error():
    # Sanity check: coordinator.async_send_command() catches
    # DeepalApiError broadly, so DeepalCommandNotReady (missing/broken
    # login private key) must be a subclass for that to work.
    assert issubclass(
        api_errors.DeepalCommandNotReady, api_errors.DeepalApiError
    )
