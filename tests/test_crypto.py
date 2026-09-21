"""Unit tests for the remote-command crypto helpers in crypto.py.

Pure-function tests using real RSA keypairs generated on the fly (the
`cryptography` package has no Home Assistant dependency). No network,
no vehicle, no Home Assistant required.
"""

from __future__ import annotations

import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from custom_components.deepal_spain_dec import crypto


@pytest.fixture
def keypair() -> tuple[str, rsa.RSAPrivateKey]:
    """A throwaway RSA keypair, standing in for the login keypair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return private_pem, private_key


def test_decrypt_with_private_key_round_trips(keypair):
    private_pem, private_key = keypair
    plaintext = "FAKE-SERIAL-1234567890"

    ciphertext = private_key.public_key().encrypt(
        plaintext.encode(), padding.PKCS1v15()
    )
    ciphertext_b64 = base64.b64encode(ciphertext).decode()

    assert (
        crypto.decrypt_with_private_key(private_pem, ciphertext_b64)
        == plaintext
    )


def test_decrypt_with_private_key_wrong_key_never_recovers_plaintext(
    keypair,
):
    # NOTE: decrypting with the wrong RSA key does not reliably raise an
    # exception — with PKCS1v15 padding, garbage output occasionally
    # passes the padding check and even decodes as valid UTF-8 (observed
    # empirically at roughly a 1-2% rate across random keypairs). So the
    # only property we can assert with certainty is that the wrong key
    # never recovers the real plaintext — not that it always raises.
    _, private_key = keypair
    other_private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=1024
    )
    other_pem = other_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    plaintext = "hello"
    ciphertext = private_key.public_key().encrypt(
        plaintext.encode(), padding.PKCS1v15()
    )
    ciphertext_b64 = base64.b64encode(ciphertext).decode()

    try:
        result = crypto.decrypt_with_private_key(
            other_pem, ciphertext_b64
        )
    except ValueError:
        return  # Decryption failing outright is the common, expected case.

    assert result != plaintext


def test_sign_command_payload_matches_expected_canonical_string(
    keypair,
):
    private_pem, private_key = keypair
    payload = {
        "command": "air",
        "enabled": True,
        "runTime": 30,
        "targetTemp": 220,
        "windMode": 1,
        "seriralNo": "FAKE-SERIAL-1234567890",
        "vehicleId": "veh-123",
    }

    signature_b64 = crypto.sign_command_payload(private_pem, payload)
    signature = base64.b64decode(signature_b64)

    # Sorted alphabetically, "command" excluded, booleans lowercased.
    expected_canonical = (
        "enabled=true&runTime=30&seriralNo=FAKE-SERIAL-1234567890"
        "&targetTemp=220&vehicleId=veh-123&windMode=1"
    )

    # If sign_command_payload used a different canonical string, this
    # verification against the *expected* one would fail.
    private_key.public_key().verify(
        signature,
        expected_canonical.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )


def test_sign_command_payload_excludes_command_class_and_sign(
    keypair,
):
    private_pem, _ = keypair
    base_payload = {
        "enabled": True,
        "seriralNo": "SN",
        "vehicleId": "veh-123",
    }

    signature = crypto.sign_command_payload(
        private_pem, {**base_payload, "command": "air"}
    )

    # Changing "command" must not change the signature: it's excluded
    # from the canonical string.
    assert (
        crypto.sign_command_payload(
            private_pem,
            {**base_payload, "command": "something-else"},
        )
        == signature
    )

    # A previously-set "sign" field must not affect a fresh signature
    # either (it would if it weren't excluded, since sign_command_payload
    # doesn't clear it from the input payload).
    assert (
        crypto.sign_command_payload(
            private_pem,
            {**base_payload, "command": "air", "sign": "stale"},
        )
        == signature
    )


def test_sign_command_payload_none_becomes_literal_null(keypair):
    private_pem, private_key = keypair
    payload = {"a": None, "vehicleId": "veh-123"}

    signature_b64 = crypto.sign_command_payload(private_pem, payload)
    signature = base64.b64decode(signature_b64)

    expected_canonical = "a=null&vehicleId=veh-123"

    private_key.public_key().verify(
        signature,
        expected_canonical.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
