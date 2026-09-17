"""Button platform for Deepal Spain DEC."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity


REFRESH_BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="refresh_vehicle_data",
    translation_key="refresh_vehicle_data",
    name="Actualizar datos del vehículo",
    icon="mdi:refresh",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain refresh button."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        [
            DeepalSpainRefreshButton(
                coordinator,
                REFRESH_BUTTON_DESCRIPTION,
            )
        ]
    )


class DeepalSpainRefreshButton(
    DeepalSpainEntity,
    ButtonEntity,
):
    """Button used to refresh Deepal vehicle telemetry."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the refresh button."""
        super().__init__(
            coordinator,
            description.key,
        )

        self.entity_description = description

    async def async_press(self) -> None:
        """Request an immediate telemetry update."""
        await self.coordinator.async_request_refresh()
