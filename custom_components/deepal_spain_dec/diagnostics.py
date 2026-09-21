"""Diagnostics support for Deepal Spain DEC.

Exposed in the Home Assistant UI from the device page: the ⋮ menu next to
the vehicle device offers "Download diagnostics", which downloads the JSON
this module builds.

The report has three sections, meant to make it easy to compare a
before/after capture while testing a change on the real car:

- "vehiculo": basic vehicle info (VIN and internal IDs redacted).
- "entidades_mapeadas": the current value of every field already exposed
  as a Home Assistant entity (from DeepalTelemetry).
- "parametros_en_bruto": every raw key the vehicle sent in the last
  successful update, value included.
- "sin_mapear": the subset of "parametros_en_bruto" that has no entity yet
  (raw keys minus telemetry.MAPPED_KEYS) — the candidates to map next.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CAC_TOKEN,
    CONF_CAC_USER_ID,
    CONF_CA_USER_ID,
    CONF_DEVICE_ID,
    CONF_EMAIL,
    CONF_MOBILE,
    CONF_PRIVATE_KEY,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    CONF_VEHICLE_ID,
    CONF_VEHICLE_IMAGE_URL,
    CONF_VEHICLE_VIN,
    DOMAIN,
)
from .coordinator import DeepalSpainCoordinator
from .telemetry import MAPPED_KEYS

REDACTED = "**REDACTED**"

# Exact key names known today to identify the vehicle, the account, or
# something usable to authenticate as the user.
TO_REDACT = {
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_CAC_TOKEN,
    CONF_PRIVATE_KEY,
    CONF_USER_ID,
    CONF_CA_USER_ID,
    CONF_CAC_USER_ID,
    CONF_DEVICE_ID,
    CONF_EMAIL,
    CONF_MOBILE,
    CONF_VEHICLE_ID,
    CONF_VEHICLE_VIN,
    CONF_VEHICLE_IMAGE_URL,
    "vin",
    "vehicle_id",
    "image_url",
}

# Belt-and-braces on top of TO_REDACT: any key whose name *contains* one
# of these (case-insensitive) is redacted too, even if nobody remembered
# to add its exact name above. Cross-checked against another open-source
# Deepal integration (ha-deepal-alternative), which takes the same
# substring approach in its own redact.py. This is what will
# automatically cover the control PIN field once phase 2 (doors/windows/
# trunk, see docs/remote-control.md) introduces it — "pin" already
# matches, on purpose.
SENSITIVE_SUBSTRINGS = (
    "token",
    "password",
    "secret",
    "private_key",
    "pin",
    "serial",
    "vin",
    "device_id",
    "user_id",
    "email",
    "mobile",
)


def _is_sensitive_key(key: Any) -> bool:
    """Return True if this key should be redacted, by exact name or substring."""
    if key in TO_REDACT:
        return True

    key_lower = str(key).lower()
    return any(marker in key_lower for marker in SENSITIVE_SUBSTRINGS)


def _redact(value: Any) -> Any:
    """Recursively redact a diagnostics value by key name.

    Unlike homeassistant.components.diagnostics.async_redact_data (exact
    key matches only), this also catches anything whose key merely
    *contains* a sensitive marker — see SENSITIVE_SUBSTRINGS above.
    """
    if isinstance(value, dict):
        return {
            key: REDACTED if _is_sensitive_key(key) else _redact(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [_redact(item) for item in value]

    return value


def _mapped_entities(coordinator: DeepalSpainCoordinator) -> dict[str, Any]:
    """Return the current value of every mapped telemetry field."""
    if coordinator.data is None:
        return {}

    mapped = dataclasses.asdict(coordinator.data)

    last_update = mapped.get("last_update")
    if last_update is not None:
        mapped["last_update"] = last_update.isoformat()

    return mapped


def _raw_and_unmapped(
    coordinator: DeepalSpainCoordinator,
) -> tuple[dict[str, Any], list[str]]:
    """Return the raw vehicle payload plus the keys with no entity yet."""
    raw = dict(coordinator.last_raw_parameters)
    unmapped = sorted(set(raw) - MAPPED_KEYS)
    return raw, unmapped


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: DeepalSpainCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    vehicle = dataclasses.asdict(coordinator.vehicle)
    raw_parameters, unmapped_keys = _raw_and_unmapped(coordinator)

    diagnostics = {
        "vehiculo": vehicle,
        "entidades_mapeadas": _mapped_entities(coordinator),
        "parametros_en_bruto": raw_parameters,
        "sin_mapear": unmapped_keys,
        "config_entry_data": dict(entry.data),
    }

    return _redact(diagnostics)
