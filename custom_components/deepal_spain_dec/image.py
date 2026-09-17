"""Image platform for Deepal Spain DEC."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain vehicle image."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    if not coordinator.vehicle.image_url:
        return

    async_add_entities(
        [
            DeepalSpainVehicleImage(
                coordinator,
            )
        ]
    )


class DeepalSpainVehicleImage(
    DeepalSpainEntity,
    ImageEntity,
):
    """Representation of the Deepal vehicle image."""

    _attr_name = "Imagen del vehículo"
    _attr_translation_key = "vehicle_image"

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
    ) -> None:
        """Initialize the vehicle image."""
        DeepalSpainEntity.__init__(
            self,
            coordinator,
            "vehicle_image",
        )

        ImageEntity.__init__(
            self,
            coordinator.hass,
        )

    @property
    def image_url(self) -> str | None:
        """Return the vehicle image URL."""
        return self.coordinator.vehicle.image_url

    @property
    def image_last_updated(self) -> datetime | None:
        """Return the timestamp used to refresh the image cache."""
        if not self.image_url:
            return None

        telemetry = self.coordinator.data

        if telemetry and telemetry.last_update:
            return telemetry.last_update

        return datetime.now(UTC)
