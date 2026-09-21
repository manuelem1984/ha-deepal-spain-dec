"""Deepal Spain DEC integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DeepalApiClient
from .assistant_exposure import (
    async_apply_assistant_exposure_to_entry,
)
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
from .models import DeepalSession, DeepalVehicle


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

    # Apply once for entities that already existed (e.g. after a
    # restart); new entities apply it themselves as they're added
    # (see DeepalSpainEntity.async_added_to_hass). Both are no-ops
    # until the user has opened the integration's Options at least
    # once.
    async_apply_assistant_exposure_to_entry(hass, entry)

    entry.async_on_unload(
        entry.add_update_listener(_async_options_updated)
    )

    return True


async def _async_options_updated(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Re-apply voice-assistant exposure right after the options change."""
    async_apply_assistant_exposure_to_entry(hass, entry)


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
