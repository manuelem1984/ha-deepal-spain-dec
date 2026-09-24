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
from homeassistant.helpers import entity_registry as er

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


def _battery_entity_id(
    hass: HomeAssistant,
    vehicle_id: str,
) -> str | None:
    """Look up the battery sensor's current entity_id for one vehicle.

    Entity descriptions only fix a unique_id
    (f"{vehicle_id}_battery_level", see entity.py); the entity_id
    itself is assigned by Home Assistant and can be renamed by the
    user, so it has to be resolved through the entity registry rather
    than guessed from the vehicle_id/key directly.
    """
    return er.async_get(hass).async_get_entity_id(
        "sensor",
        DOMAIN,
        f"{vehicle_id}_battery_level",
    )


def _general_card(
    entry_options: dict[str, Any],
    battery_entity_id: str | None,
) -> dict[str, Any]:
    """Build the first ("General") card: title plus a battery indicator.

    The battery indicator — percentage text followed by a battery
    icon, both colored by charge level (red below 10%, yellow 10-30%,
    green above 30%) and the icon shape stepped in the same 0/10/20/
    .../100 increments Home Assistant's own battery icons use — is
    built as a Jinja template inside the markdown card's content,
    right-aligned, since a plain markdown card is the simplest way to
    mix a templated icon with arbitrary layout (a flexbox row) inside
    the same bordered card as the title, rather than a separate card.
    If the battery entity can't be found (e.g. still starting up),
    the indicator is left out rather than shipping a template that
    references a non-existent entity.
    """
    content = ""

    if battery_entity_id:
        content = (
            "<div style='display:flex;justify-content:flex-end;"
            "align-items:center;gap:6px;font-size:1.1em;'>\n"
            f"{{%- set batt = states('{battery_entity_id}') | "
            "int(0) -%}\n"
            "{%- if batt < 10 -%}{%- set batt_color = "
            "'var(--error-color, red)' -%}\n"
            "{%- elif batt <= 30 -%}{%- set batt_color = "
            "'var(--warning-color, orange)' -%}\n"
            "{%- else -%}{%- set batt_color = "
            "'var(--success-color, green)' -%}{%- endif -%}\n"
            "{%- set batt_step = (batt / 10) | round(0, 'floor') "
            "| int * 10 -%}\n"
            "{%- if batt_step <= 0 -%}{%- set batt_icon = "
            "'mdi:battery-outline' -%}\n"
            "{%- elif batt_step >= 100 -%}{%- set batt_icon = "
            "'mdi:battery' -%}\n"
            "{%- else -%}{%- set batt_icon = "
            "'mdi:battery-' ~ batt_step -%}{%- endif -%}\n"
            "<span style='color:{{ batt_color }};'>{{ batt }}%"
            "</span>\n"
            "<ha-icon icon='{{ batt_icon }}' "
            "style='color:{{ batt_color }};'></ha-icon>\n"
            "</div>"
        )

    return {
        "type": "markdown",
        "title": _vehicle_card_title(entry_options),
        "content": content,
    }


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

        vehicle_id = coordinator.vehicle.vehicle_id
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
                            _general_card(
                                entry.options,
                                _battery_entity_id(
                                    hass, vehicle_id
                                ),
                            )
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
