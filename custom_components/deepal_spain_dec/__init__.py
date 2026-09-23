"""Deepal Spain DEC integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DeepalApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CAC_TOKEN,
    CONF_CAC_USER_ID,
    CONF_CA_USER_ID,
    CONF_DEVICE_ID,
    CONF_MQTT_ENABLED,
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
from . import dashboard
from .models import DeepalSession, DeepalVehicle


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up the Deepal Spain DEC integration (not entry-specific).

    Called once at Home Assistant startup regardless of how many (if
    any) config entries exist — the right place to register the
    "DEC - Vehículos" sidebar panel a single time. Also writes an
    (initially empty, since no entry has loaded yet at this point)
    dashboard file so the panel doesn't 404 before the first entry
    finishes setting up.
    """
    dashboard.async_register_panel(hass)
    await dashboard.async_write_dashboard(hass)
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

    # Defensive: async_setup already registers the panel once at HA
    # startup, but a config entry can also be added at runtime
    # without a restart, before async_setup would otherwise run for
    # this domain — registering again here is a harmless no-op.
    dashboard.async_register_panel(hass)
    await dashboard.async_write_dashboard(hass)

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
    needed for image_last_updated to actually advance.
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

        await dashboard.async_write_dashboard(hass)

    return unload_successful
