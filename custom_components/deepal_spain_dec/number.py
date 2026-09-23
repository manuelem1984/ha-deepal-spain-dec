"""Number platform for Deepal Spain DEC (seat heat/vent level).

First cut of remote control added in v1.3.1b4, alongside switch.py.
No PIN required for any of these — see docs/remote-control.md.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
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

MIN_SEAT_LEVEL = 0
MAX_SEAT_LEVEL = 3


def _seat_command(
    coordinator: DeepalSpainCoordinator,
    level: int,
    *,
    api_method_name: str,
    is_driver: bool,
) -> Callable[[], Coroutine[Any, Any, str]]:
    """Build a command_factory for one seat heat/vent number.

    level 0 turns the seat off — the switch is still sent as 0, but
    the level itself must be omitted entirely (see
    api.DeepalApiClient._seat_payload for why: the server rejects an
    explicit level of 0).
    """
    switch = 1 if level > 0 else 0
    api_level = level if level > 0 else None
    method = getattr(coordinator.api, api_method_name)

    if is_driver:
        return lambda: method(
            coordinator.vehicle.vehicle_id,
            master_switch=switch,
            master_level=api_level,
        )

    return lambda: method(
        coordinator.vehicle.vehicle_id,
        copilot_switch=switch,
        copilot_level=api_level,
    )


@dataclass(
    frozen=True,
    kw_only=True,
)
class DeepalSeatLevelDescription(NumberEntityDescription):
    """Describe a Deepal seat heat/vent level number."""

    value_fn: Callable[[DeepalTelemetry], int | None]
    optimistic_field: str
    api_method_name: str
    is_driver: bool


SEAT_LEVEL_DESCRIPTIONS: tuple[DeepalSeatLevelDescription, ...] = (
    DeepalSeatLevelDescription(
        key="driver_seat_heat_level",
        translation_key="driver_seat_heat_level",
        name="Calefacción asiento conductor",
        icon="mdi:car-seat-heater",
        native_min_value=MIN_SEAT_LEVEL,
        native_max_value=MAX_SEAT_LEVEL,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.driver_seat_heat_level,
        optimistic_field="driver_seat_heat_level",
        api_method_name="control_seats_heat",
        is_driver=True,
    ),
    DeepalSeatLevelDescription(
        key="passenger_seat_heat_level",
        translation_key="passenger_seat_heat_level",
        name="Calefacción asiento acompañante",
        icon="mdi:car-seat-heater",
        native_min_value=MIN_SEAT_LEVEL,
        native_max_value=MAX_SEAT_LEVEL,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.passenger_seat_heat_level,
        optimistic_field="passenger_seat_heat_level",
        api_method_name="control_seats_heat",
        is_driver=False,
    ),
    DeepalSeatLevelDescription(
        key="driver_seat_vent_level",
        translation_key="driver_seat_vent_level",
        name="Ventilación asiento conductor",
        icon="mdi:car-seat-cooler",
        native_min_value=MIN_SEAT_LEVEL,
        native_max_value=MAX_SEAT_LEVEL,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.driver_seat_vent_level,
        optimistic_field="driver_seat_vent_level",
        api_method_name="control_seats_wind",
        is_driver=True,
    ),
    DeepalSeatLevelDescription(
        key="passenger_seat_vent_level",
        translation_key="passenger_seat_vent_level",
        name="Ventilación asiento acompañante",
        icon="mdi:car-seat-cooler",
        native_min_value=MIN_SEAT_LEVEL,
        native_max_value=MAX_SEAT_LEVEL,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.passenger_seat_vent_level,
        optimistic_field="passenger_seat_vent_level",
        api_method_name="control_seats_wind",
        is_driver=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain seat level numbers."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        DeepalSpainSeatLevelNumber(coordinator, description)
        for description in SEAT_LEVEL_DESCRIPTIONS
    )


class DeepalSpainSeatLevelNumber(
    DeepalSpainEntity,
    NumberEntity,
):
    """A seat heating or ventilation level (0 = off, 1-3 = level)."""

    entity_description: DeepalSeatLevelDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: DeepalSeatLevelDescription,
    ) -> None:
        """Initialize the seat level number."""
        super().__init__(coordinator, description.key)

        self.entity_description = description

    @property
    def native_value(self) -> int | None:
        """Return the current seat heat/vent level."""
        data = self.coordinator.data

        if data is None:
            return None

        return self.entity_description.value_fn(data)

    async def async_set_native_value(self, value: float) -> None:
        """Set the seat heat/vent level (0 turns it off)."""
        level = max(
            MIN_SEAT_LEVEL,
            min(MAX_SEAT_LEVEL, int(value)),
        )

        await self.coordinator.async_send_command(
            _seat_command(
                self.coordinator,
                level,
                api_method_name=self.entity_description.api_method_name,
                is_driver=self.entity_description.is_driver,
            ),
            optimistic_update={
                self.entity_description.optimistic_field: level
            },
        )
