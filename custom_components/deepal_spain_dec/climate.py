"""Climate platform for Deepal Spain DEC (cabin air conditioner).

First cut of remote control: this command does not require the
control PIN (unlike doors/windows/trunk, not implemented yet). See
docs/remote-control.md for what's confirmed and what isn't.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity

# Reasonable bounds for the cabin AC; not yet confirmed against the
# real vehicle's own min/max.
MIN_TEMPERATURE_C = 16.0
MAX_TEMPERATURE_C = 32.0
DEFAULT_TARGET_TEMPERATURE_C = 22.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain cabin climate entity."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities([DeepalSpainClimate(coordinator)])


class DeepalSpainClimate(DeepalSpainEntity, ClimateEntity):
    """Remote control of the cabin air conditioner.

    Only on/off and target temperature are wired up here; fan speed
    stays read-only for now (sensor.fan_speed) — setting it remotely
    would need confirming the windMode values against the real
    vehicle first.
    """

    _attr_name = "Climatización"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
    )
    _attr_min_temp = MIN_TEMPERATURE_C
    _attr_max_temp = MAX_TEMPERATURE_C
    _attr_target_temperature_step = 0.5

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator, "cabin_climate")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return whether the cabin AC is on or off."""
        data = self.coordinator.data

        if data is None or data.climate_on is None:
            return None

        return (
            HVACMode.HEAT_COOL
            if data.climate_on
            else HVACMode.OFF
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the cabin's current temperature."""
        data = self.coordinator.data
        return data.inside_temperature_c if data else None

    @property
    def target_temperature(self) -> float | None:
        """Return the requested cabin temperature."""
        data = self.coordinator.data
        return (
            data.climate_target_temperature_c
            if data
            else None
        )

    async def async_set_hvac_mode(
        self,
        hvac_mode: HVACMode,
    ) -> None:
        """Turn the cabin air conditioner on or off."""
        target = (
            self.target_temperature
            or DEFAULT_TARGET_TEMPERATURE_C
        )
        turning_on = hvac_mode != HVACMode.OFF

        await self.coordinator.async_send_command(
            lambda: self.coordinator.api.control_air_conditioner(
                self.coordinator.vehicle.vehicle_id,
                enabled=turning_on,
                target_temp_c=target,
            ),
            optimistic_update={"climate_on": turning_on},
        )

    async def async_set_temperature(
        self,
        **kwargs: Any,
    ) -> None:
        """Set the target cabin temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)

        if temperature is None:
            return

        await self.coordinator.async_send_command(
            lambda: self.coordinator.api.control_air_conditioner(
                self.coordinator.vehicle.vehicle_id,
                enabled=True,
                target_temp_c=float(temperature),
            ),
            optimistic_update={
                "climate_on": True,
                "climate_target_temperature_c": float(temperature),
            },
        )
