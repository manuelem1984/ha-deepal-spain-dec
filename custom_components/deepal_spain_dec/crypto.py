"""Cryptographic helpers for Deepal Spain DEC."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from typing import Any

from cryptography.hazmat.primitives import (
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
