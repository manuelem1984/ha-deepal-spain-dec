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
# an independent reference implementation; not yet confirmed by us
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
# by reading an independent reference client directly.
CONTROL_RESULT = (
    "/intl-app-gw/intl-app-car-control/api/control/control-result"
)

# The following four, added in v1.3.1b4, were reverse-engineered by
# reading an independent reference client's code rather than
# cross-checking against captured MQTT payloads like the read-only
# fields — none of
# these have been sent to the real vehicle yet, see
# docs/remote-control.md.
CONTROL_SEATS_HEAT = (
    "/intl-app-gw/intl-app-car-control/api/control/seats/heat"
)
CONTROL_SEATS_WIND = (
    "/intl-app-gw/intl-app-car-control/api/control/seats/wind"
)
CONTROL_STEERING_WHEEL_HEAT = (
    "/intl-app-gw/intl-app-car-control/api/control/steering-wheel/heat"
)
CONTROL_DEFROST = (
    "/intl-app-gw/intl-app-car-control/api/control/defrost"
)

# Different gateway (car-condition, not car-control): a richer,
# on-demand snapshot of the vehicle used by the official app itself.
# Confirmed by reading an independent reference implementation:
# for the S05, a handful of MQTT fields (seat heat/vent, steering
# wheel heat, front defrost) are unreliable — sometimes sentinel
# values, sometimes simply not kept in sync with what the app shows
# — while this endpoint's equivalent fields are. See
# coordinator._async_overlay_condition() and docs/remote-control.md.
CONDITION_OVERLAY = (
    "/intl-app-gw/intl-app-car-condition/api/vehicle/condition"
)

# PIN-gated endpoints (doors, windows, trunk) — the only commands that
# need the remote-control PIN exchanged for an "rcToken" first. See
# docs/remote-control.md, "Comandos con PIN", for the full mechanism.
# The PIN exchange itself:
GET_SECURITY_CODE_STATUS = (
    "/intl-app-gw/intl-app-car-control/api/security-code/get-status"
)
CHECK_CONTROL_CODE = (
    "/intl-app-gw/intl-app-car-control/api/security-code/check-code"
)
# The three commands themselves. Endpoint paths follow the same
# control/* convention as every other signed command; the exact
# payload shape for windows in particular (per-window field names)
# is a best-effort guess pending confirmation against a real
# vehicle — see api.py's control_windows() docstring.
CONTROL_DOORS = (
    "/intl-app-gw/intl-app-car-control/api/control/doors"
)
CONTROL_WINDOWS = (
    "/intl-app-gw/intl-app-car-control/api/control/windows"
)
CONTROL_TRUNK = (
    "/intl-app-gw/intl-app-car-control/api/control/trunk"
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

# PIN de control remoto (puertas, ventanillas, maletero) — todo el
# bloque es opcional y viene desactivado por defecto. Ver
# config_flow.DeepalSpainOptionsFlow y docs/remote-control.md.
CONF_PIN_ENABLED = "pin_enabled"
CONF_CONTROL_PIN = "control_pin"
CONF_PIN_MODE = "pin_mode"
CONF_ARM_DURATION = "arm_duration_seconds"
CONF_ARM_NOTIFY = "arm_notify"

# Opción A: comandos con PIN directos, sin verificación previa.
PIN_MODE_UNSAFE = "unsafe"
# Opción B: hace falta "armar" primero (entidad lock
# "Desbloqueo Acciones PIN"), como un mando de garaje.
PIN_MODE_SAFE = "safe"
PIN_MODES = {
    PIN_MODE_UNSAFE: "No segura (comandos directos)",
    PIN_MODE_SAFE: "Segura (verificación en dos pulsaciones)",
}
DEFAULT_PIN_MODE = PIN_MODE_UNSAFE

# Cuánto dura "armado" el candado de la Opción B antes de rebloquearse
# solo. Siempre arranca bloqueado al iniciar Home Assistant.
ARM_DURATION_OPTIONS = ["10", "20", "30", "60"]
DEFAULT_ARM_DURATION_SECONDS = 30
DEFAULT_ARM_NOTIFY = False

# Vehicle trim and color, chosen by the user in the integration's
# Options (not provided by Deepal's API) so the bundled photo can
# match their exact car instead of a generic stock shot. Both are
# optional — if either is unset, image.py falls back to Deepal's own
# image_url (when available) or the generic bundled photo, exactly as
# before this feature existed.
CONF_VEHICLE_TRIM = "vehicle_trim"
CONF_VEHICLE_COLOR = "vehicle_color"

# Officially the S05 is sold in Spain as Pro / Max / Max AWD, but Max
# and Max AWD are mechanically different (rear-wheel vs. all-wheel
# drive) while looking exactly the same from the outside — so they
# share the same set of bundled photos (see VEHICLE_TRIM_PHOTO_GROUP).
VEHICLE_TRIMS = {
    "pro": "Pro",
    "max": "Max",
    "max_awd": "Max AWD",
}
VEHICLE_TRIM_PHOTO_GROUP = {
    "pro": "pro",
    "max": "max",
    "max_awd": "max",
}

# The five official exterior colors of the Deepal S05.
VEHICLE_COLORS = {
    "andromeda_blue": "Andromeda Blue",
    "deep_space_black": "Deep Space Black",
    "ganymade_grey": "Ganymade Grey",
    "mercury_silver": "Mercury Silver",
    "moonlight_white": "Moonlight White",
}

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
    "number",
    "switch",
    "lock",
    "cover",
]
