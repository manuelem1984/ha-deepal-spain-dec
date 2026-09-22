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

from .const import (
    CONF_VEHICLE_COLOR,
    CONF_VEHICLE_TRIM,
    DOMAIN,
    VEHICLE_TRIM_PHOTO_GROUP,
)
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity

ASSETS_DIR = Path(__file__).parent / "assets"

# Generic stock photo, used whenever Deepal's API does not return an
# image URL for the vehicle (observed to happen on some accounts) AND
# the user hasn't picked a trim/color in the integration's Options —
# so the image entity always has something to show.
FALLBACK_IMAGE_PATH = ASSETS_DIR / "deepal_s05.png"

# Per-trim, per-color bundled photos, added in v1.3.1 — see
# docs/vehicle-photos.md for the exact file naming and how to add a
# missing one.
VEHICLE_PHOTOS_DIR = ASSETS_DIR / "vehicle_photos"


def _matching_photo_path(
    trim: str | None,
    color: str | None,
) -> Path | None:
    """Return the bundled photo for this trim+color, if one exists.

    Both settings are needed — a trim without a color (or vice versa)
    isn't enough to pick a specific photo, so this returns None and
    the caller falls back to the API image or the generic photo
    instead. Max and Max AWD look identical from the outside and
    share the same photos (VEHICLE_TRIM_PHOTO_GROUP).
    """
    if not trim or not color:
        return None

    photo_group = VEHICLE_TRIM_PHOTO_GROUP.get(trim)

    if not photo_group:
        return None

    path = VEHICLE_PHOTOS_DIR / f"{photo_group}_{color}.png"

    return path if path.is_file() else None


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
                entry,
            )
        ]
    )


class DeepalSpainVehicleImage(
    DeepalSpainEntity,
    ImageEntity,
):
    """Representation of the Deepal vehicle image.

    Shown, in order of preference:
    1. The bundled photo matching the trim + color chosen in the
       integration's Options (added in v1.3.1) — the most likely to
       actually look like this specific car.
    2. The photo Deepal's API returns for the vehicle, when available.
    3. A generic bundled stock photo of the S05, so this entity — and
       the picture on the device page — always exists regardless.
    """

    _attr_name = "Imagen del vehículo"
    _attr_translation_key = "vehicle_image"

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        entry: ConfigEntry,
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

        self._entry = entry

        if not self._bundled_photo_path:
            return

        # Static bundled image (either the trim/color match or the
        # generic fallback): content type and "last updated" only
        # need to be set once, at startup.
        self._attr_content_type = "image/png"
        self._attr_image_last_updated = datetime.now(UTC)

    @property
    def _bundled_photo_path(self) -> Path | None:
        """Return the bundled photo to show, unless the API has one."""
        if self.coordinator.vehicle.image_url:
            return None

        matching = _matching_photo_path(
            self._entry.options.get(CONF_VEHICLE_TRIM),
            self._entry.options.get(CONF_VEHICLE_COLOR),
        )

        return matching or FALLBACK_IMAGE_PATH

    @property
    def image_url(self) -> str | None:
        """Return the vehicle image URL, when Deepal's API provides one."""
        return self.coordinator.vehicle.image_url

    async def async_image(self) -> bytes | None:
        """Return the image bytes.

        Delegates to the base class (fetches image_url over HTTP) when
        Deepal's API gave us a URL; otherwise reads the matching
        bundled photo from disk.
        """
        if self.coordinator.vehicle.image_url:
            return await super().async_image()

        return await self.hass.async_add_executor_job(
            self._bundled_photo_path.read_bytes
        )

    @property
    def image_last_updated(self) -> datetime | None:
        """Return the timestamp used to refresh the image cache."""
        if self.coordinator.vehicle.image_url:
            telemetry = self.coordinator.data

            if telemetry and telemetry.last_update:
                return telemetry.last_update

            return datetime.now(UTC)

        return self._attr_image_last_updated


