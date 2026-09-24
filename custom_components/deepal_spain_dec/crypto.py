"""Cryptographic helpers for Deepal Spain DEC."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from typing import Any

from cryptography.hazmat.primitives import (
    hashes,
    padding as symmetric_padding,
    serialization,
)
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)

from .const import REQUEST_ENCRYPTION_PUBLIC_KEY


def generate_login_keypair() -> tuple[str, str]:
    """Generate the RSA key pair required by the Deepal login flow."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    public_key_body = (
        "\n".join(
            line
            for line in public_pem.splitlines()
            if "BEGIN" not in line and "END" not in line
        )
        + "\n"
    )

    return private_pem, public_key_body


def encrypt_login_value(value: str) -> str:
    """Encrypt an email address or mobile number for the Deepal API."""
    public_key = serialization.load_der_public_key(
        base64.b64decode(REQUEST_ENCRYPTION_PUBLIC_KEY)
    )

    encrypted_value = public_key.encrypt(
        value.encode(),
        padding.PKCS1v15(),
    )

    return base64.b64encode(encrypted_value).decode()


def decode_base64(value: str) -> bytes:
    """Decode Base64 data, adding missing padding when required."""
    padding_length = (4 - len(value) % 4) % 4
    return base64.b64decode(
        value + ("=" * padding_length)
    )


def decrypt_mqtt_payload(
    encrypted: str,
    secret_key: str,
    request_id: str,
) -> list[dict[str, Any]]:
    """Decrypt and decompress an encrypted Deepal MQTT payload."""
    initialization_vector = hashlib.md5(
        request_id.encode()
    ).digest()

    decryptor = Cipher(
        algorithms.AES(secret_key.encode()),
        modes.CBC(initialization_vector),
    ).decryptor()

    encrypted_bytes = decode_base64(encrypted)

    padded_plaintext = (
        decryptor.update(encrypted_bytes)
        + decryptor.finalize()
    )

    unpadder = symmetric_padding.PKCS7(128).unpadder()

    plaintext = (
        unpadder.update(padded_plaintext)
        + unpadder.finalize()
    )

    compressed_data = decode_base64(
        plaintext.decode().strip()
    )

    decoded_data = json.loads(
        gzip.decompress(compressed_data).decode()
    )

    if not isinstance(decoded_data, list):
        return []

    return decoded_data


def encrypt_mqtt_payload(
    data: list[dict[str, Any]],
    secret_key: str,
    request_id: str,
) -> str:
    """Compress and encrypt a Deepal MQTT payload."""
    json_data = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()

    compressed_data = gzip.compress(json_data)
    compressed_base64 = base64.b64encode(compressed_data)

    padder = symmetric_padding.PKCS7(128).padder()

    padded_data = (
        padder.update(compressed_base64)
        + padder.finalize()
    )

    initialization_vector = hashlib.md5(
        request_id.encode()
    ).digest()

    encryptor = Cipher(
        algorithms.AES(secret_key.encode()),
        modes.CBC(initialization_vector),
    ).encryptor()

    encrypted_data = (
        encryptor.update(padded_data)
        + encryptor.finalize()
    )

    return base64.b64encode(encrypted_data).decode()


# ------------------------------------------------------------------
# Remote commands
# ------------------------------------------------------------------
#
# Reverse-engineered by cross-checking with an independent reference
# implementation that targets the same backend (same base URLs as
# ours). Not yet
# confirmed by us against a real command sent to a vehicle — see
# docs/remote-control.md.

# Fields the official app never includes when computing a command's
# signature, regardless of what else is in the payload.
_SIGNATURE_EXCLUDED_KEYS = frozenset({"sign", "class", "command"})


def decrypt_with_private_key(
    private_key_pem: str,
    ciphertext_base64: str,
) -> str:
    """Decrypt a value with our own login private key (PKCS#1 v1.5).

    Used for the encrypted vehicle serial number the app fetches right
    before signing a remote command.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )

    ciphertext = decode_base64(
        "".join(ciphertext_base64.split())
    )

    try:
        return private_key.decrypt(
            ciphertext,
            padding.PKCS1v15(),
        ).decode().strip()
    except ValueError as err:
        raise ValueError(
            "Could not decrypt the value with the login private key"
        ) from err


def sign_command_payload(
    private_key_pem: str,
    payload: dict[str, Any],
) -> str:
    """Sign a remote-command payload the same way the official app does.

    Canonical string: every key of `payload` except `sign`, `class` and
    `command`, sorted alphabetically, joined as "key=value&key=value..."
    (booleans lowercased, ``None`` written as the literal string
    "null"). Signed with RSA-SHA256 (PKCS#1 v1.5) using the same
    private key generated at login, base64-encoded.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
    )

    parts = []

    for key in sorted(payload):
        if key in _SIGNATURE_EXCLUDED_KEYS:
            continue

        value = payload[key]

        if isinstance(value, bool):
            value = str(value).lower()
        elif value is None:
            value = "null"

        parts.append(f"{key}={value}")

    canonical = "&".join(parts)

    signature = private_key.sign(
        canonical.encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode()
