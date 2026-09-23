"""Lovelace dashboard registration and generation for Deepal Spain DEC.

First cut, added in v1.3.1b7: registers a single YAML-mode Lovelace
dashboard ("DEC - Vehículos") in the sidebar, with one tab (view) per
configured vehicle — titled with its VIN, per an explicit design
choice: a friendlier per-vehicle nickname would need an API endpoint
we haven't found yet (see docs/roadmap.md). Each tab has, for now, a
single card showing "Deepal S05 <trim> <color>" and nothing else —
everything else in the dashboard design is deliberately left empty,
to be filled in over the next few betas.
"""

from __future__ import annotations

import logging
from typing import Any

import yaml
from homeassistant.components import frontend
from homeassistant.core import HomeAssistant

from .const import (
    CONF_VEHICLE_COLOR,
    CONF_VEHICLE_TRIM,
    DASHBOARD_FILENAME,
    DASHBOARD_ICON,
    DASHBOARD_TITLE,
    DASHBOARD_URL_PATH,
    DOMAIN,
    VEHICLE_COLORS,
    VEHICLE_TRIMS,
)

_LOGGER = logging.getLogger(__name__)


def async_register_panel(hass: HomeAssistant) -> None:
    """Register the "DEC - Vehículos" sidebar panel, once.

    Safe to call more than once (e.g. on every config entry setup, or
    if more than one vehicle is configured): Home Assistant raises
    ValueError if a panel with this URL path is already registered,
    which is exactly the "already done" case this ignores.
    """
    try:
        frontend.async_register_built_in_panel(
            hass,
            component_name="lovelace",
            sidebar_title=DASHBOARD_TITLE,
            sidebar_icon=DASHBOARD_ICON,
            frontend_url_path=DASHBOARD_URL_PATH,
            config={
                "mode": "yaml",
                "filename": DASHBOARD_FILENAME,
            },
            require_admin=False,
        )
    except ValueError:
        # Already registered — fine, nothing to do.
        pass


def _vehicle_card_title(entry_options: dict[str, Any]) -> str:
    """Build the one card's title: "Deepal S05 <trim> <color>".

    "Deepal" and "S05" are always fixed; trim/color come from what the
    user picked in Options (config_flow.DeepalSpainOptionsFlow) — if
    either hasn't been set, it's simply left out rather than shown as
    a placeholder.
    """
    parts = ["Deepal", "S05"]

    trim_key = entry_options.get(CONF_VEHICLE_TRIM)
    if trim_key in VEHICLE_TRIMS:
        parts.append(VEHICLE_TRIMS[trim_key])

    color_key = entry_options.get(CONF_VEHICLE_COLOR)
    if color_key in VEHICLE_COLORS:
        parts.append(VEHICLE_COLORS[color_key])

    return " ".join(parts)


def _build_dashboard_config(hass: HomeAssistant) -> dict[str, Any]:
    """Build the full YAML-mode dashboard: one view (tab) per vehicle.

    Iterates every currently loaded config entry for this domain —
    not just the one just set up or torn down — so the dashboard
    always reflects every configured vehicle regardless of load
    order.
    """
    domain_data: dict[str, Any] = hass.data.get(DOMAIN, {})
    views: list[dict[str, Any]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = domain_data.get(entry.entry_id)

        if coordinator is None:
            continue

        vin = coordinator.vehicle.vin or entry.entry_id

        views.append(
            {
                "title": vin,
                "path": vin,
                "type": "sections",
                "max_columns": 3,
                "sections": [
                    {
                        "type": "grid",
                        "cards": [
                            {
                                "type": "markdown",
                                "title": _vehicle_card_title(
                                    entry.options
                                ),
                                "content": "",
                            }
                        ],
                    }
                ],
            }
        )

    return {"title": DASHBOARD_TITLE, "views": views}


async def async_write_dashboard(hass: HomeAssistant) -> None:
    """(Re)write the dashboard's YAML file for every configured vehicle.

    Best-effort: a write failure (e.g. a read-only config directory)
    is logged and otherwise ignored, rather than failing config entry
    setup over a dashboard file.
    """
    config = _build_dashboard_config(hass)
    path = hass.config.path(DASHBOARD_FILENAME)

    def _write() -> None:
        with open(path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(
                config,
                handle,
                allow_unicode=True,
                sort_keys=False,
            )

    try:
        await hass.async_add_executor_job(_write)
    except OSError as error:
        _LOGGER.warning(
            "Could not write the Deepal Spain DEC dashboard file "
            "(%s): %s",
            path,
            error,
        )
