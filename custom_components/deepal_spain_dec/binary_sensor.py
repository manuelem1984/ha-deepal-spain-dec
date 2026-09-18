"""Binary sensor platform for Deepal Spain DEC."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
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
class DeepalBinarySensorDescription(
    BinarySensorEntityDescription
):
    """Describe a Deepal Spain binary sensor."""

    value_fn: Callable[
        [DeepalTelemetry],
        bool | None,
    ]

    # Optional per-state icon override. When set, these take priority
    # over `icon` / the device_class default (e.g. a lock icon shaped
    # like an actual car door instead of a generic padlock).
    icon_on: str | None = None
    icon_off: str | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[
    DeepalBinarySensorDescription,
    ...,
] = (
    DeepalBinarySensorDescription(
        key="vehicle_connected",
        translation_key="vehicle_connected",
        name="Vehículo conectado",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.connected,
    ),
    DeepalBinarySensorDescription(
        key="engine_on",
        translation_key="engine_on",
        name="Motor encendido",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.engine_on,
    ),
    DeepalBinarySensorDescription(
        key="charging",
        translation_key="charging",
        name="Cargando",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: data.charging,
    ),
    DeepalBinarySensorDescription(
        key="front_left_door",
        translation_key="front_left_door",
        name="Ventanilla Delantera Izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-door",
        value_fn=lambda data: data.front_left_door,
    ),
    DeepalBinarySensorDescription(
        key="front_right_door",
        translation_key="front_right_door",
        name="Ventanilla Delantera Derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-door",
        value_fn=lambda data: data.front_right_door,
    ),
    DeepalBinarySensorDescription(
        key="rear_left_door",
        translation_key="rear_left_door",
        name="Ventanilla Trasera Izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-door",
        value_fn=lambda data: data.rear_left_door,
    ),
    DeepalBinarySensorDescription(
        key="rear_right_door",
        translation_key="rear_right_door",
        name="Ventanilla Trasera Derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-door",
        value_fn=lambda data: data.rear_right_door,
    ),
    DeepalBinarySensorDescription(
        key="trunk",
        translation_key="trunk",
        name="Maletero",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda data: data.trunk_open,
    ),
    DeepalBinarySensorDescription(
        key="driver_locked",
        translation_key="driver_locked",
        name="Puerta del Conductor Bloqueo",
        device_class=BinarySensorDeviceClass.LOCK,
        icon_on="mdi:car-door-lock",
        icon_off="mdi:car-door-lock-open",
        value_fn=lambda data: data.driver_locked,
    ),
    DeepalBinarySensorDescription(
        key="passenger_locked",
        translation_key="passenger_locked",
        name="Puerta del Acompañante Bloqueo",
        device_class=BinarySensorDeviceClass.LOCK,
        icon_on="mdi:car-door-lock",
        icon_off="mdi:car-door-lock-open",
        value_fn=lambda data: data.passenger_locked,
    ),
    DeepalBinarySensorDescription(
        key="front_left_window",
        translation_key="front_left_window",
        name="Ventanilla delantera izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda data: data.front_left_window,
    ),
    DeepalBinarySensorDescription(
        key="front_right_window",
        translation_key="front_right_window",
        name="Ventanilla delantera derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda data: data.front_right_window,
    ),
    DeepalBinarySensorDescription(
        key="rear_left_window",
        translation_key="rear_left_window",
        name="Ventanilla trasera izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda data: data.rear_left_window,
    ),
    DeepalBinarySensorDescription(
        key="rear_right_window",
        translation_key="rear_right_window",
        name="Ventanilla trasera derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda data: data.rear_right_window,
    ),
    DeepalBinarySensorDescription(
        key="high_beam",
        translation_key="high_beam",
        name="Luz de carretera",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda data: data.high_beam,
    ),
    DeepalBinarySensorDescription(
        key="low_beam",
        translation_key="low_beam",
        name="Luz de cruce",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda data: data.low_beam,
    ),
    DeepalBinarySensorDescription(
        key="position_lamp",
        translation_key="position_lamp",
        name="Luz de posición",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda data: data.position_lamp,
    ),
    DeepalBinarySensorDescription(
        key="left_indicator",
        translation_key="left_indicator",
        name="Intermitente izquierdo",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda data: data.left_indicator,
    ),
    DeepalBinarySensorDescription(
        key="right_indicator",
        translation_key="right_indicator",
        name="Intermitente derecho",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda data: data.right_indicator,
    ),
    DeepalBinarySensorDescription(
        key="hood_open",
        translation_key="hood_open",
        name="Capó",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda data: data.hood_open,
    ),
    DeepalBinarySensorDescription(
        key="climate_on",
        translation_key="climate_on",
        name="Aire acondicionado encendido",
        icon_on="mdi:air-conditioner",
        icon_off="mdi:fan-off",
        value_fn=lambda data: data.climate_on,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deepal Spain binary sensors."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        DeepalSpainBinarySensor(
            coordinator,
            description,
        )
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class DeepalSpainBinarySensor(
    DeepalSpainEntity,
    BinarySensorEntity,
):
    """Representation of a Deepal Spain binary sensor."""

    entity_description: DeepalBinarySensorDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: DeepalBinarySensorDescription,
    ) -> None:
        """Initialize a Deepal Spain binary sensor."""
        super().__init__(
            coordinator,
            description.key,
        )

        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        data = self.coordinator.data

        if data is None:
            return None

        return self.entity_description.value_fn(data)

    @property
    def icon(self) -> str | None:
        """Return a per-state icon when the description defines one."""
        description = self.entity_description

        if (
            description.icon_on is None
            and description.icon_off is None
        ):
            return description.icon

        is_on = self.is_on

        if is_on is None:
            return description.icon

        return (
            description.icon_on
            if is_on
            else description.icon_off
        )

