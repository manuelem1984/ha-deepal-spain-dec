"""Unit tests for the remote-command flow in api.py.

Uses a hand-rolled fake aiohttp session (no real network, no extra test
dependency like pytest-asyncio or aioresponses) — just enough of
aiohttp's ClientSession/ClientResponse shape for DeepalApiClient.post()
to work against it. Real RSA keypairs, same as tests/test_crypto.py.

NOTE: importing api.py requires the real aiohttp package (not just its
API shape) — CI installs it in lint.yaml alongside pytest and
cryptography.
"""

from __future__ import annotations

import asyncio
import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from custom_components.deepal_spain_dec.api import DeepalApiClient
from custom_components.deepal_spain_dec.api_errors import (
    DeepalApiError,
    DeepalCommandNotReady,
    DeepalRateLimitError,
)


class FakeResponse:
    """Stand-in for an aiohttp.ClientResponse, used as an async context manager."""

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    async def json(self, content_type=None):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class FakeSession:
    """Stand-in for aiohttp.ClientSession.

    Returns one queued FakeResponse per call to post(), in order, and
    records every request made so tests can inspect what was actually
    sent (url, headers, JSON body).
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[tuple[str, dict]] = []

    def post(self, url, **kwargs):
        self.requests.append((url, kwargs))
        return self._responses.pop(0)

    def sent_json(self, index: int) -> dict:
        """Parse the JSON body of the index-th request sent."""
        return json.loads(self.requests[index][1]["data"])


@pytest.fixture
def private_key_pem() -> tuple[str, rsa.RSAPrivateKey]:
    """A throwaway RSA keypair, standing in for the login keypair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=1024
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return pem, private_key


def _encrypted_serial_response(private_key, serial: str) -> dict:
    """Build the fake JSON body Deepal's serial-no/get endpoint returns.

    Encrypted with the *public* half of our own login keypair, mirroring
    what the real server does before sending the serial number back.
    """
    ciphertext = private_key.public_key().encrypt(
        serial.encode(), padding.PKCS1v15()
    )
    return {
        "success": True,
        "data": base64.b64encode(ciphertext).decode(),
    }


def test_signed_command_without_private_key_raises_not_ready():
    async def run():
        session = FakeSession([])
        client = DeepalApiClient(
            session, device_id="dev-1", access_token="tok"
        )
        # private_key_pem intentionally left unset.

        with pytest.raises(DeepalCommandNotReady):
            await client.control_condition_inquiry("veh-123")

        # Must fail before ever contacting the server.
        assert session.requests == []

    asyncio.run(run())


def test_control_condition_inquiry_sends_signed_payload(
    private_key_pem,
):
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse(
                    {"success": True, "data": {"commandId": "cmd-42"}}
                ),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )

        command_id = await client.control_condition_inquiry("veh-123")

        assert command_id == "cmd-42"
        assert len(session.requests) == 2

        sent_payload = session.sent_json(1)
        assert sent_payload["seriralNo"] == serial
        assert sent_payload["vehicleId"] == "veh-123"
        assert sent_payload["command"] == "COMMAND_GET_NEW_CONDITION"
        assert "sign" in sent_payload

        # The signature itself must verify against the exact payload
        # sent (minus sign/class/command), the same way
        # tests/test_crypto.py checks sign_command_payload directly.
        signature = base64.b64decode(sent_payload["sign"])
        canonical = "&".join(
            f"{key}={sent_payload[key]}"
            for key in sorted(sent_payload)
            if key not in {"sign", "class", "command"}
        )
        private_key.public_key().verify(
            signature,
            canonical.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

    asyncio.run(run())


def test_control_air_conditioner_encodes_target_temperature_in_tenths(
    private_key_pem,
):
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse(
                    {"success": True, "data": {"commandId": "cmd-1"}}
                ),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )

        await client.control_air_conditioner(
            "veh-123", enabled=True, target_temp_c=22.5
        )

        sent_payload = session.sent_json(1)
        # Documented in docs/remote-control.md as unconfirmed against
        # the real vehicle: the command payload uses tenths of a
        # degree, unlike the telemetry field (direct degrees).
        assert sent_payload["targetTemp"] == 225
        assert sent_payload["enabled"] is True

    asyncio.run(run())


def test_signed_command_raises_api_error_without_command_id(
    private_key_pem,
):
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse({"success": True, "data": {}}),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )

        with pytest.raises(DeepalApiError):
            await client.control_condition_inquiry("veh-123")

    asyncio.run(run())


def test_get_serial_number_raises_when_response_is_not_a_string():
    async def run():
        session = FakeSession(
            [FakeResponse({"success": True, "data": {"oops": 1}})]
        )
        client = DeepalApiClient(
            session, device_id="dev-1", access_token="tok"
        )

        with pytest.raises(DeepalApiError):
            await client.get_serial_number()

    asyncio.run(run())


# ------------------------------------------------------------------
# PIN-gated commands (doors, windows, trunk) — see
# docs/remote-control.md, "Comandos con PIN".
# ------------------------------------------------------------------


def test_pin_gated_command_without_pin_raises_not_ready():
    async def run():
        session = FakeSession([])
        client = DeepalApiClient(
            session, device_id="dev-1", access_token="tok"
        )
        # No private key AND no control_pin set — either alone would
        # already refuse this, but control_pin is checked first for
        # a PIN-gated command.
        client.private_key_pem = "unused"

        with pytest.raises(DeepalCommandNotReady):
            await client.control_doors("veh-123", True)

        # Must fail before ever contacting the server.
        assert session.requests == []

    asyncio.run(run())


def test_control_doors_exchanges_pin_and_signs_rc_token(
    private_key_pem,
):
    """No cached rc_token: exchanges the PIN first, then signs with it."""
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    {"success": True, "data": {"retryQuantity": 5}}
                ),
                FakeResponse(
                    {"success": True, "data": {"rcToken": "rc-1"}}
                ),
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse(
                    {
                        "success": True,
                        "data": {"commandId": "cmd-doors-1"},
                    }
                ),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )
        client.control_pin = "1234"

        command_id = await client.control_doors("veh-123", True)

        assert command_id == "cmd-doors-1"
        assert len(session.requests) == 4
        assert client.rc_token == "rc-1"

        sent_payload = session.sent_json(3)
        assert sent_payload["rcToken"] == "rc-1"
        assert sent_payload["lock"] is True
        assert sent_payload["command"] == "doors"

        # rcToken is part of what gets signed too, not a separate step.
        signature = base64.b64decode(sent_payload["sign"])
        canonical = "&".join(
            f"{key}={str(sent_payload[key]).lower() if isinstance(sent_payload[key], bool) else sent_payload[key]}"
            for key in sorted(sent_payload)
            if key not in {"sign", "class", "command"}
        )
        private_key.public_key().verify(
            signature,
            canonical.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

    asyncio.run(run())


def test_control_trunk_reuses_cached_rc_token(private_key_pem):
    """A cached rc_token skips the PIN exchange entirely."""
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse(
                    {
                        "success": True,
                        "data": {"commandId": "cmd-trunk-1"},
                    }
                ),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )
        client.control_pin = "1234"
        client.rc_token = "rc-cached"

        command_id = await client.control_trunk("veh-123", True)

        assert command_id == "cmd-trunk-1"
        # Only the serial number and the command itself — no PIN
        # exchange calls at all.
        assert len(session.requests) == 2

    asyncio.run(run())


def test_control_windows_refreshes_stale_rc_token_and_retries_once(
    private_key_pem,
):
    """A reused rc_token rejected by the server is refreshed and retried."""
    pem, private_key = private_key_pem
    serial = "FAKE-SERIAL-1234567890"

    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    _encrypted_serial_response(private_key, serial)
                ),
                FakeResponse(
                    {
                        "success": False,
                        "code": "COMMON_1_1_01_099",
                        "msg": "rcToken expired",
                    }
                ),
                FakeResponse(
                    {"success": True, "data": {"retryQuantity": 5}}
                ),
                FakeResponse(
                    {"success": True, "data": {"rcToken": "rc-new"}}
                ),
                FakeResponse(
                    {
                        "success": True,
                        "data": {"commandId": "cmd-windows-1"},
                    }
                ),
            ]
        )
        client = DeepalApiClient(
            session,
            device_id="dev-1",
            access_token="tok",
            private_key_pem=pem,
        )
        client.control_pin = "1234"
        client.rc_token = "rc-old"

        command_id = await client.control_windows(
            "veh-123", window="leftFront", open_window=True
        )

        assert command_id == "cmd-windows-1"
        assert client.rc_token == "rc-new"
        assert session.sent_json(4)["rcToken"] == "rc-new"

    asyncio.run(run())


def test_check_control_code_refuses_locally_when_no_attempts_left():
    async def run():
        session = FakeSession(
            [
                FakeResponse(
                    {"success": True, "data": {"retryQuantity": 0}}
                ),
            ]
        )
        client = DeepalApiClient(
            session, device_id="dev-1", access_token="tok"
        )

        with pytest.raises(DeepalRateLimitError):
            await client.check_control_code("1234")

        # Never even tries to submit the PIN itself.
        assert len(session.requests) == 1

    asyncio.run(run())
