"""Switch platform for Deepal Spain DEC (steering wheel heat, defrost).

First cut of remote control added in v1.3.1b4, alongside number.py.
No PIN required for either of these — see docs/remote-control.md.
Front defrost is exposed here as an entity even though the command
is rarely wired up in other implementations for this backend.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity
from .models import DeepalTelemetry


@dataclass(
    frozen=True,
    kw_only=True,
)
class DeepalSwitchDescription(SwitchEntityDescription):
    """Describe a Deepal on/off remote-control switch."""

    value_fn: Callable[[DeepalTelemetry], bool | None]
    optimistic_field: str
    api_method_name: str


SWITCH_DESCRIPTIONS: tuple[DeepalSwitchDescription, ...] = (
    DeepalSwitchDescription(
        key="steering_wheel_heat",
        translation_key="steering_wheel_heat",
        name="Volante calefactado",
        icon="mdi:steering",
        value_fn=lambda data: data.steering_wheel_heat_on,
        optimistic_field="steering_wheel_heat_on",
        api_method_name="control_steering_wheel_heat",
    ),
    DeepalSwitchDescription(
        key="front_defrost",
        translation_key="front_defrost",
        name="Desempañado delantero",
        icon="mdi:car-defrost-front",
        value_fn=lambda data: data.front_defrost_on,
        optimistic_field="front_defrost_on",
        api_method_name="control_defrost",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain remote-control switches."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        DeepalSpainSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    )


class DeepalSpainSwitch(
    DeepalSpainEntity,
    SwitchEntity,
):
    """A simple on/off remote-control switch."""

    entity_description: DeepalSwitchDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: DeepalSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description.key)

        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return whether this feature is currently on."""
        data = self.coordinator.data

        if data is None:
            return None

        return self.entity_description.value_fn(data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn this feature on."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn this feature off."""
        await self._async_set(False)

    async def _async_set(self, enabled: bool) -> None:
        """Send the command and update optimistically."""
        method: Callable[
            [str, bool],
            Coroutine[Any, Any, str],
        ] = getattr(
            self.coordinator.api,
            self.entity_description.api_method_name,
        )

        await self.coordinator.async_send_command(
            lambda: method(
                self.coordinator.vehicle.vehicle_id,
                enabled,
            ),
            optimistic_update={
                self.entity_description.optimistic_field: enabled
            },
        )
