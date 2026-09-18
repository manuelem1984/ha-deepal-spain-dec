"""Base entity for Deepal Spain DEC."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SHORT_NAME, VERSION
from .coordinator import DeepalSpainCoordinator


class DeepalSpainEntity(
    CoordinatorEntity[DeepalSpainCoordinator]
):
    """Base entity for a Deepal Spain vehicle."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize the Deepal Spain entity."""
        super().__init__(coordinator)

        self._entity_key = entity_key
        self._attr_unique_id = (
            f"{coordinator.vehicle.vehicle_id}_{entity_key}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the Deepal vehicle."""
        vehicle = self.coordinator.vehicle

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    vehicle.vehicle_id,
                )
            },
            name=(
                vehicle.model_name
                or vehicle.vin
                or "Deepal España"
            ),
            manufacturer="Comunidad Deepal España",
            model="Changan Deepal S05",
            serial_number=vehicle.vin,
            configuration_url=(
                "https://t.me/deepalespana_general"
            ),
            sw_version=VERSION,
            hw_version=SHORT_NAME,
        )
