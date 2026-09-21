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

from .api_errors import DeepalApiError
from .const import DOMAIN, FLASH_HONK_BEE, FLASH_HONK_FLASH
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity


REFRESH_BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="refresh_vehicle_data",
    translation_key="refresh_vehicle_data",
    name="Actualizar datos del vehículo",
    icon="mdi:refresh",
)

FLASH_LIGHTS_BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="flash_lights",
    translation_key="flash_lights",
    name="Parpadear luces",
    icon="mdi:car-light-alert",
)

HONK_HORN_BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="honk_horn",
    translation_key="honk_horn",
    name="Tocar el claxon",
    icon="mdi:bullhorn",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain buttons."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        [
            DeepalSpainRefreshButton(
                coordinator,
                REFRESH_BUTTON_DESCRIPTION,
            ),
            DeepalSpainFlashLightsButton(
                coordinator,
                FLASH_LIGHTS_BUTTON_DESCRIPTION,
            ),
            DeepalSpainHonkHornButton(
                coordinator,
                HONK_HORN_BUTTON_DESCRIPTION,
            ),
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
        """Nudge the vehicle for fresh data, then request an update.

        The nudge (control_condition_inquiry) is a signed remote
        command like the others in this file; it's wrapped in
        try/except here (rather than going through
        coordinator.async_send_command) so a missing/undecryptable
        login private key never breaks this button's original,
        simpler behaviour — it just falls back to a plain poll.
        """
        try:
            await self.coordinator.api.control_condition_inquiry(
                self.coordinator.vehicle.vehicle_id
            )
        except DeepalApiError:
            pass

        await self.coordinator.async_request_refresh()


class DeepalSpainFlashLightsButton(
    DeepalSpainEntity,
    ButtonEntity,
):
    """Button used to flash the vehicle's lights."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the flash-lights button."""
        super().__init__(
            coordinator,
            description.key,
        )

        self.entity_description = description

    async def async_press(self) -> None:
        """Flash the vehicle's lights."""
        await self.coordinator.async_send_command(
            self.coordinator.api.control_flashing_honking(
                self.coordinator.vehicle.vehicle_id,
                FLASH_HONK_FLASH,
            ),
            # Doesn't change any telemetry field: skip the
            # inquiry-and-poll that async_send_command otherwise does.
            refresh_after=False,
        )


class DeepalSpainHonkHornButton(
    DeepalSpainEntity,
    ButtonEntity,
):
    """Button used to sound the vehicle's horn."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the honk-horn button."""
        super().__init__(
            coordinator,
            description.key,
        )

        self.entity_description = description

    async def async_press(self) -> None:
        """Sound the vehicle's horn."""
        await self.coordinator.async_send_command(
            self.coordinator.api.control_flashing_honking(
                self.coordinator.vehicle.vehicle_id,
                FLASH_HONK_BEE,
            ),
            refresh_after=False,
        )
