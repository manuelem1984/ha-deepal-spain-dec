"""Lock platform for Deepal Spain DEC (doors, and the arming lock).

Added in v1.3.1 alongside cover.py: the PIN-gated remote-control
block (doors/windows/trunk) — see docs/remote-control.md for the
full design (the PIN exchange, "Opción A" vs "Opción B", the
"Desbloqueo Acciones PIN" arming lock).

Neither entity here is created unless the PIN block is enabled in
Options (config_flow.DeepalSpainOptionsFlow); the arming lock is
further gated on "Opción B" (safe) mode specifically, since it does
nothing in "Opción A".
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import (
    CONF_PIN_ENABLED,
    CONF_PIN_MODE,
    DOMAIN,
    PIN_MODE_SAFE,
)
from .coordinator import DeepalSpainCoordinator
from .entity import DeepalSpainEntity
from .telemetry import any_door_unlocked


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Deepal Spain lock entities.

    Nothing is created at all unless the PIN block is enabled — a
    lock entity that always refuses itself would just be confusing
    clutter on the device page.
    """
    if not entry.options.get(CONF_PIN_ENABLED):
        return

    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    entities: list[DeepalSpainEntity] = [
        DeepalSpainDoorLock(coordinator)
    ]

    if entry.options.get(CONF_PIN_MODE) == PIN_MODE_SAFE:
        entities.append(DeepalSpainArmLock(coordinator))

    async_add_entities(entities)


class DeepalSpainDoorLock(
    DeepalSpainEntity,
    LockEntity,
):
    """The car's central locking (all doors at once).

    Payload shape confirmed by cross-checking a reference
    implementation for this backend; not yet tried against a real
    vehicle. Reads its current state from the same telemetry fields
    the existing "Cierre centralizado" binary_sensor already uses
    (any_door_unlocked), rather than duplicating that logic.
    """

    _attr_name = "Bloqueo de puertas"

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
    ) -> None:
        """Initialize the door lock."""
        super().__init__(coordinator, "door_lock")

    @property
    def is_locked(self) -> bool | None:
        """Return whether the car is currently locked."""
        data = self.coordinator.data

        if data is None:
            return None

        unlocked = any_door_unlocked(data)

        if unlocked is None:
            return None

        return not unlocked

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock every door."""
        await self._async_set_locked(True)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock every door."""
        await self._async_set_locked(False)

    async def _async_set_locked(self, locked: bool) -> None:
        """Send the lock/unlock command.

        requires_arming=True: in "Opción B" (safe) PIN mode, this is
        refused unless "Desbloqueo Acciones PIN" has been unlocked
        first — see coordinator.async_send_command().
        """
        await self.coordinator.async_send_command(
            lambda: self.coordinator.api.control_doors(
                self.coordinator.vehicle.vehicle_id,
                locked,
            ),
            optimistic_update={
                "driver_locked": locked,
                "passenger_locked": locked,
            },
            requires_arming=True,
        )


class DeepalSpainArmLock(
    DeepalSpainEntity,
    LockEntity,
):
    """"Desbloqueo Acciones PIN" — the "Opción B" arming lock.

    Unlocking it doesn't send any command to the vehicle at all: it
    just opens a short window (configurable in Options) during which
    the other PIN-gated commands (doors, windows, trunk) are allowed
    to run — see coordinator.async_arm()/async_disarm() and
    docs/remote-control.md. Always starts locked on every Home
    Assistant restart or reload, on purpose — the armed state is
    never persisted.
    """

    _attr_name = "Desbloqueo Acciones PIN"
    _attr_icon = "mdi:lock"

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
    ) -> None:
        """Initialize the arming lock."""
        super().__init__(coordinator, "pin_arm_lock")

    @property
    def is_locked(self) -> bool:
        """Return whether PIN-gated commands are currently blocked."""
        return not self.coordinator.is_armed

    async def async_lock(self, **kwargs: Any) -> None:
        """Re-lock PIN-gated commands immediately."""
        self.coordinator.async_disarm()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Arm PIN-gated commands for the configured duration."""
        self.coordinator.async_arm()
