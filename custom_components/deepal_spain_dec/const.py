"""Constants for Deepal Spain DEC."""

import json
from pathlib import Path

DOMAIN = "deepal_spain_dec"
NAME = "DEC Deepal S05 - Comunidad Deepal España"

# Short form of NAME, used only for the "Hardware" field on the device
# page — the full name there would be redundant with the integration
# title shown right above it.
SHORT_NAME = "DEC Deepal S05"

# Single source of truth for the version: read straight from
# manifest.json so it only has to be updated in one place.
_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
VERSION = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))["version"]

# Spain configuration
SPAIN_COUNTRY = "ES"
SPAIN_DIAL_CODE = "34"

# Application configuration
DEFAULT_LANGUAGE = "en_US"
DEFAULT_APP_VERSION = "V1.11.0"

# Deepal cloud endpoints
BASE_URL = "https://m.iov.changanauto.com.de"
CA_BASE_URL = "https://ca-m.iov.changanauto.com.de"

# Remote-control endpoints (reverse-engineered by cross-checking with
# another open-source Deepal integration; not yet confirmed by us
# against a real vehicle — see docs/remote-control.md). All of these
# require a signed payload (see crypto.sign_command_payload) but none
# of them need the control PIN ("rcToken") — that's only required for
# doors/windows/trunk, not implemented yet.
CONTROL_GET_SERIAL_NO = (
    "/intl-app-gw/intl-app-car-control/api/serial-no/get"
)
CONTROL_AIR_CONDITIONER = (
    "/intl-app-gw/intl-app-car-control/api/control/air-conditioner"
)
CONTROL_CONDITION_INQUIRY = (
    "/intl-app-gw/intl-app-car-control/api/control/condition-inquiry"
)
CONTROL_FLASHING_HONKING = (
    "/intl-app-gw/intl-app-car-control/api/control/flashing-honking"
)
# Unlike the other control/* endpoints, this one is a plain
# authenticated POST — no serial number, no RSA signature. Confirmed
# by reading ha-deepal-alternative's own client code directly.
CONTROL_RESULT = (
    "/intl-app-gw/intl-app-car-control/api/control/control-result"
)

# control_flashing_honking() action types.
FLASH_HONK_OFF = 0
FLASH_HONK_FLASH = 1
FLASH_HONK_BEE = 2
FLASH_HONK_FLASH_BEE = 3

# HTTP configuration
REQUEST_TIMEOUT = 30

# Public key used to encrypt login values
REQUEST_ENCRYPTION_PUBLIC_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkyhr43cBPTJ3jLiYsmbUwUp74cMJIOju5vqVzgtuK63Q99qV6iVT8wN5cXlyMtWI2mfOmhIao/fUN821im69MfOHsWXdqQEo5e9v654GPw+bju0pCphEPtD1I0VcyS34QkAu04urSun2U1q3Dr2OICLVWSnLa+01ioKxkaB0D209zXcls2eFQpvRAWm7xxVsoqzSwqp+neu5quOpn+eO/bW0TxcSQ8VZcDEUvadRTLSR0eOWgRuHIBiD2RGqPIPzKCm5A14q1qhxUZ8U0pmYe0Sx7eMy4RVe2iW7fnjc6pxTUMBkercSL26mevYouuCKqyie+LVQAtGa29RMl/lyiwIDAQAB"
)

# Configuration entry fields
CONF_LOGIN_METHOD = "login_method"
CONF_EMAIL = "email"
CONF_MOBILE = "mobile"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_CAC_TOKEN = "cac_token"
CONF_USER_ID = "user_id"
CONF_CA_USER_ID = "ca_user_id"
CONF_CAC_USER_ID = "cac_user_id"
CONF_DEVICE_ID = "device_id"
CONF_PRIVATE_KEY = "private_key"
CONF_VEHICLE_ID = "vehicle_id"
CONF_VEHICLE_VIN = "vehicle_vin"
CONF_VEHICLE_MODEL = "vehicle_model"
CONF_VEHICLE_IMAGE_URL = "vehicle_image_url"
CONF_MQTT_ENABLED = "mqtt_enabled"

# Spain login methods
LOGIN_METHOD_EMAIL = "email"
LOGIN_METHOD_SMS = "sms"

# Home Assistant platforms
PLATFORMS = [
    "sensor",
    "binary_sensor",
    "button",
    "image",
    "climate",
]
