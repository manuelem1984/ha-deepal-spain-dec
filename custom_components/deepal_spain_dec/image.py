"""Image platform for Deepal Spain DEC."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity

# Bundled stock photo, used whenever Deepal's API does not return an
# image URL for the vehicle (observed to happen on some accounts) so
# the image entity always has something to show.
FALLBACK_IMAGE_PATH = (
    Path(__file__).parent / "assets" / "deepal_s05.png"
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain vehicle image."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

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
    """Representation of the Deepal vehicle image.

    Shows the photo Deepal's API returns for the vehicle when
    available; otherwise falls back to a bundled stock photo of the
    S05, so this entity — and the picture on the device page — always
    exists instead of silently not being created at all.
    """

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

        if not coordinator.vehicle.image_url:
            # Static bundled image: content type and "last updated"
            # only need to be set once, at startup.
            self._attr_content_type = "image/png"
            self._attr_image_last_updated = datetime.now(UTC)

    @property
    def image_url(self) -> str | None:
        """Return the vehicle image URL, when Deepal's API provides one."""
        return self.coordinator.vehicle.image_url

    async def async_image(self) -> bytes | None:
        """Return the image bytes.

        Delegates to the base class (fetches image_url over HTTP) when
        Deepal's API gave us a URL; otherwise reads the bundled photo
        from disk.
        """
        if self.coordinator.vehicle.image_url:
            return await super().async_image()

        return await self.hass.async_add_executor_job(
            FALLBACK_IMAGE_PATH.read_bytes
        )

    @property
    def image_last_updated(self) -> datetime | None:
        """Return the timestamp used to refresh the image cache."""
        if not self.coordinator.vehicle.image_url:
            return self._attr_image_last_updated

        telemetry = self.coordinator.data

        if telemetry and telemetry.last_update:
            return telemetry.last_update

        return datetime.now(UTC)

