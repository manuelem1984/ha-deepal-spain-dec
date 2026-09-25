"""Cover platform for Deepal Spain DEC (windows, trunk).

Added in v1.3.1 alongside lock.py — see docs/remote-control.md for
the full PIN-gated remote-control design. Nothing here is created
unless the PIN block is enabled in Options
(config_flow.DeepalSpainOptionsFlow).

These add *writable* control on top of telemetry fields that already
exist as read-only binary_sensor entities since v1.3.1b13 ("Ventanilla
Delantera Izquierda", "Maletero", etc.) — both are kept side by side
rather than replacing the existing sensors, to avoid a breaking
change; see docs/roadmap.md for a possible future cleanup.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import CONF_PIN_ENABLED, DOMAIN
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity
from .models import DeepalTelemetry


@dataclass(
    frozen=True,
    kw_only=True,
)
class DeepalWindowDescription(CoverEntityDescription):
    """Describe a Deepal window cover."""

    is_open_fn: Callable[[DeepalTelemetry], bool | None]
    window_position: str


WINDOW_DESCRIPTIONS: tuple[DeepalWindowDescription, ...] = (
    DeepalWindowDescription(
        key="front_left_window",
        translation_key="front_left_window_cover",
        name="Ventanilla Delantera Izquierda",
        device_class=CoverDeviceClass.WINDOW,
        is_open_fn=lambda data: data.front_left_window_open,
        window_position="leftFront",
    ),
    DeepalWindowDescription(
        key="front_right_window",
        translation_key="front_right_window_cover",
        name="Ventanilla Delantera Derecha",
        device_class=CoverDeviceClass.WINDOW,
        is_open_fn=lambda data: data.front_right_window_open,
        window_position="rightFront",
    ),
    DeepalWindowDescription(
        key="rear_left_window",
        translation_key="rear_left_window_cover",
        name="Ventanilla Trasera Izquierda",
        device_class=CoverDeviceClass.WINDOW,
        is_open_fn=lambda data: data.rear_left_window_open,
        window_position="leftRear",
    ),
    DeepalWindowDescription(
        key="rear_right_window",
        translation_key="rear_right_window_cover",
        name="Ventanilla Trasera Derecha",
        device_class=CoverDeviceClass.WINDOW,
        is_open_fn=lambda data: data.rear_right_window_open,
        window_position="rightRear",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain window and trunk covers."""
    if not entry.options.get(CONF_PIN_ENABLED):
        return

    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    entities: list[DeepalSpainEntity] = [
        DeepalSpainWindowCover(coordinator, description)
        for description in WINDOW_DESCRIPTIONS
    ]
    entities.append(DeepalSpainTrunkCover(coordinator))

    async_add_entities(entities)


class DeepalSpainWindowCover(
    DeepalSpainEntity,
    CoverEntity,
):
    """One window, controlled individually.

    Payload shape for control_windows() is a best-effort guess, not
    yet confirmed against a real vehicle — see
    api.DeepalApiClient.control_windows().
    """

    entity_description: DeepalWindowDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: DeepalWindowDescription,
    ) -> None:
        """Initialize the window cover."""
        super().__init__(coordinator, description.key)

        self.entity_description = description

    @property
    def is_closed(self) -> bool | None:
        """Return whether the window is currently closed."""
        data = self.coordinator.data

        if data is None:
            return None

        is_open = self.entity_description.is_open_fn(data)

        if is_open is None:
            return None

        return not is_open

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Lower the window."""
        await self._async_set_open(True)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Raise the window."""
        await self._async_set_open(False)

    async def _async_set_open(self, open_window: bool) -> None:
        """Send the window command.

        requires_arming=True: in "Opción B" (safe) PIN mode, this is
        refused unless "Desbloqueo Acciones PIN" has been unlocked
        first — see coordinator.async_send_command().
        """
        window_position = self.entity_description.window_position

        await self.coordinator.async_send_command(
            lambda: self.coordinator.api.control_windows(
                self.coordinator.vehicle.vehicle_id,
                window=window_position,
                open_window=open_window,
            ),
            optimistic_update={
                self.entity_description.key + "_open": open_window
            },
            requires_arming=True,
        )


class DeepalSpainTrunkCover(
    DeepalSpainEntity,
    CoverEntity,
):
    """The trunk.

    Payload shape confirmed by cross-checking a reference
    implementation for this backend; not yet tried against a real
    vehicle. Reuses the same "trunk_open" telemetry field the
    existing "Maletero" binary_sensor already reads.
    """

    _attr_name = "Maletero"
    _attr_device_class = CoverDeviceClass.DOOR

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
    ) -> None:
        """Initialize the trunk cover."""
        super().__init__(coordinator, "trunk_cover")

    @property
    def is_closed(self) -> bool | None:
        """Return whether the trunk is currently closed."""
        data = self.coordinator.data

        if data is None or data.trunk_open is None:
            return None

        return not data.trunk_open

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the trunk."""
        await self._async_set_open(True)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the trunk."""
        await self._async_set_open(False)

    async def _async_set_open(self, open_trunk: bool) -> None:
        """Send the trunk command.

        requires_arming=True: in "Opción B" (safe) PIN mode, this is
        refused unless "Desbloqueo Acciones PIN" has been unlocked
        first — see coordinator.async_send_command().
        """
        await self.coordinator.async_send_command(
            lambda: self.coordinator.api.control_trunk(
                self.coordinator.vehicle.vehicle_id,
                open_trunk,
            ),
            optimistic_update={"trunk_open": open_trunk},
            requires_arming=True,
        )
