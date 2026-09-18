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

from homeassistant.components.diagnostics import async_redact_data
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

# Anything that identifies the vehicle, the account, or could be used to
# authenticate as the user. Applied to both the config entry data and the
# vehicle info block below.
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

    return async_redact_data(diagnostics, TO_REDACT)
