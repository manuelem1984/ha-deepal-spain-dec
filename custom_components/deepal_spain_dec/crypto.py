"""Cryptographic helpers for Deepal Spain DEC."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

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
