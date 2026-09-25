"""Deepal Spain DEC integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DeepalApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CAC_TOKEN,
    CONF_CAC_USER_ID,
    CONF_CA_USER_ID,
    CONF_CONTROL_PIN,
    CONF_DEVICE_ID,
    CONF_MQTT_ENABLED,
    CONF_PIN_ENABLED,
    CONF_PRIVATE_KEY,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    CONF_VEHICLE_ID,
    CONF_VEHICLE_IMAGE_URL,
    CONF_VEHICLE_MODEL,
    CONF_VEHICLE_VIN,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import DeepalSpainCoordinator
from . import frontend_icons
from .models import DeepalSession, DeepalVehicle

# Config-flow-only integration: async_setup() below exists purely to
# register the "dec:" custom icon set once per Home Assistant run
# (see frontend_icons.py), not to accept any YAML configuration. This
# tells Home Assistant/hassfest exactly that — a bare "domain:" line
# in configuration.yaml is rejected with a clear repair issue instead
# of being silently accepted or misread as configuration.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up the Deepal Spain DEC integration (not entry-specific).

    Called once at Home Assistant startup regardless of how many (if
    any) config entries exist — the right place to register the
    "dec:" custom icon set exactly once. See
    frontend_icons.async_register_icons() for why this must not be
    done from async_setup_entry() instead.
    """
    await frontend_icons.async_register_icons(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Deepal Spain DEC from a configuration entry."""
    api = DeepalApiClient(
        async_get_clientsession(hass),
        device_id=entry.data[CONF_DEVICE_ID],
        access_token=entry.data[CONF_ACCESS_TOKEN],
        cac_token=entry.data.get(CONF_CAC_TOKEN),
        private_key_pem=entry.data.get(CONF_PRIVATE_KEY),
    )

    if entry.options.get(CONF_PIN_ENABLED):
        # Only set when the PIN block is enabled — leaving it as None
        # otherwise makes every PIN-gated command refuse itself
        # outright (DeepalCommandNotReady), which is also why
        # lock.py/cover.py don't create those entities at all in that
        # case (see their async_setup_entry()).
        api.control_pin = entry.options.get(CONF_CONTROL_PIN)

    session = DeepalSession(
        access_token=entry.data[CONF_ACCESS_TOKEN],
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
        cac_token=entry.data.get(CONF_CAC_TOKEN),
        user_id=entry.data.get(CONF_USER_ID),
        ca_user_id=entry.data.get(CONF_CA_USER_ID),
        cac_user_id=entry.data.get(CONF_CAC_USER_ID),
    )

    vehicle = DeepalVehicle(
        vehicle_id=entry.data[CONF_VEHICLE_ID],
        vin=entry.data.get(CONF_VEHICLE_VIN),
        model_name=entry.data.get(CONF_VEHICLE_MODEL),
        image_url=entry.data.get(CONF_VEHICLE_IMAGE_URL),
        mqtt_enabled=entry.data.get(
            CONF_MQTT_ENABLED,
            False,
        ),
    )

    coordinator = DeepalSpainCoordinator(
        hass,
        entry,
        api,
        session,
        vehicle,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    entry.async_on_unload(
        entry.add_update_listener(_async_options_updated)
    )

    return True


async def _async_options_updated(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload the entry when its options change.

    Needed since v1.3.1: changing the vehicle trim/color in Options
    should swap the bundled photo shown by image.py, and the image
    entity only picks a fresh one at setup — see image.py's
    docstring for why a reload, not just re-reading the option, is
    needed for image_last_updated to actually advance. Also needed
    for the PIN block: enabling/disabling it, or switching between
    "Opción A"/"Opción B", changes which entities lock.py/cover.py
    create, and entity creation is decided once at platform setup.
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a Deepal Spain DEC configuration entry."""
    unload_successful = (
        await hass.config_entries.async_unload_platforms(
            entry,
            PLATFORMS,
        )
    )

    if unload_successful:
        domain_data = hass.data.get(DOMAIN)

        if domain_data is not None:
            domain_data.pop(entry.entry_id, None)

            if not domain_data:
                hass.data.pop(DOMAIN, None)

    return unload_successful
