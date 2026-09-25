"""Custom icon set ("dec:") for Deepal Spain DEC.

Added in v1.3.1b15: some entities (starting with "Volante calefactado")
need an icon Material Design Icons doesn't have. Rather than depending
on a separate community integration to provide it, this integration
serves its own tiny icon set directly — see icons/README.md for the
source SVGs, their licenses, and how to add a new one.

Uses Home Assistant's documented API for third-party icon sets
(window.customIconsets) — see
https://developers.home-assistant.io/blog/2020/05/09/custom-iconsets/.
Once registered, any entity can reference an icon as "dec:<name>", the
same way it would reference "mdi:<name>".
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import VERSION

_LOGGER = logging.getLogger(__name__)

_ICONS_DIR = Path(__file__).parent / "icons"
_ICONS_JS_FILENAME = "dec-icons.js"
_ICONS_URL_PATH = "/deepal_spain_dec_icons"


async def async_register_icons(hass: HomeAssistant) -> None:
    """Register the "dec:" custom icon set.

    Must only be called from async_setup() — once per Home Assistant
    run, regardless of how many vehicles (config entries) are
    configured — never from async_setup_entry(), which also runs on
    every config entry reload. Registering the same static path twice
    in one run raises RuntimeError in current Home Assistant versions
    ("Added route will never be executed, method GET is already
    registered") — a real bug other integrations have hit on this
    exact Home Assistant version by registering from the wrong place.
    Defensively swallows that specific error too, in case this is
    ever called more than once regardless.

    The served URL includes the integration's own version
    (?v=<version>) so a browser that cached an older dec-icons.js
    picks up the new one right after updating, instead of keeping a
    stale copy indefinitely.
    """
    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    _ICONS_URL_PATH,
                    str(_ICONS_DIR),
                    True,
                )
            ]
        )
    except RuntimeError as error:
        _LOGGER.debug(
            "Deepal Spain DEC icon set static path already "
            "registered, skipping: %s",
            error,
        )
        return

    add_extra_js_url(
        hass,
        f"{_ICONS_URL_PATH}/{_ICONS_JS_FILENAME}?v={VERSION}",
    )
