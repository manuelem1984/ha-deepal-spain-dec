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
from .telemetry import any_door_open, any_door_unlocked


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
        name="Motor - Estado",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon_on="mdi:engine",
        icon_off="mdi:engine-off-outline",
        value_fn=lambda data: data.engine_on,
    ),
    DeepalBinarySensorDescription(
        key="charging",
        translation_key="charging",
        name="Carga",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon_on="mdi:lightning-bolt",
        icon_off="mdi:lightning-bolt-outline",
        value_fn=lambda data: data.charging,
    ),
    DeepalBinarySensorDescription(
        key="ac_charge_connector",
        translation_key="ac_charge_connector",
        name="Conector AC",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:ev-plug-type2",
        value_fn=lambda data: data.ac_charge_connector_connected,
    ),
    DeepalBinarySensorDescription(
        key="dc_charge_connector",
        translation_key="dc_charge_connector",
        name="Conector DC",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:ev-plug-ccs2",
        value_fn=lambda data: data.dc_charge_connector_connected,
    ),
    DeepalBinarySensorDescription(
        key="front_left_door",
        translation_key="front_left_door",
        name="Puerta Delantera Izquierda",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: data.front_left_door,
    ),
    DeepalBinarySensorDescription(
        key="front_right_door",
        translation_key="front_right_door",
        name="Puerta Delantera Derecha",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: data.front_right_door,
    ),
    DeepalBinarySensorDescription(
        key="rear_left_door",
        translation_key="rear_left_door",
        name="Puerta Trasera Izquierda",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
        value_fn=lambda data: data.rear_left_door,
    ),
    DeepalBinarySensorDescription(
        key="rear_right_door",
        translation_key="rear_right_door",
        name="Puerta Trasera Derecha",
        device_class=BinarySensorDeviceClass.DOOR,
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
        key="any_door_open",
        translation_key="any_door_open",
        name="Alguna puerta abierta",
        device_class=BinarySensorDeviceClass.DOOR,
        icon_on="mdi:car-door",
        icon_off="mdi:car",
        # Four doors + trunk; see telemetry.any_door_open().
        value_fn=any_door_open,
    ),
    DeepalBinarySensorDescription(
        key="front_left_window",
        translation_key="front_left_window",
        name="Ventanilla Delantera Izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon_on="mdi:window-open-variant",
        icon_off="mdi:window-closed-variant",
        value_fn=lambda data: data.front_left_window_open,
    ),
    DeepalBinarySensorDescription(
        key="front_right_window",
        translation_key="front_right_window",
        name="Ventanilla Delantera Derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon_on="mdi:window-open-variant",
        icon_off="mdi:window-closed-variant",
        value_fn=lambda data: data.front_right_window_open,
    ),
    DeepalBinarySensorDescription(
        key="rear_left_window",
        translation_key="rear_left_window",
        name="Ventanilla Trasera Izquierda",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon_on="mdi:window-open-variant",
        icon_off="mdi:window-closed-variant",
        value_fn=lambda data: data.rear_left_window_open,
    ),
    DeepalBinarySensorDescription(
        key="rear_right_window",
        translation_key="rear_right_window",
        name="Ventanilla Trasera Derecha",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon_on="mdi:window-open-variant",
        icon_off="mdi:window-closed-variant",
        value_fn=lambda data: data.rear_right_window_open,
    ),
    DeepalBinarySensorDescription(
        key="central_locking",
        translation_key="central_locking",
        name="Cierre centralizado",
        device_class=BinarySensorDeviceClass.LOCK,
        # LOCK device class: on = unlocked, off = locked.
        icon_on="mdi:lock-open-variant",
        icon_off="mdi:lock",
        # Either front lock open; see telemetry.any_door_unlocked().
        value_fn=any_door_unlocked,
    ),
    DeepalBinarySensorDescription(
        key="driver_locked",
        translation_key="driver_locked",
        name="Puerta Delantera Izquierda Bloqueo",
        device_class=BinarySensorDeviceClass.LOCK,
        icon_on="mdi:car-door-lock",
        icon_off="mdi:car-door-lock-open",
        value_fn=lambda data: data.driver_locked,
    ),
    DeepalBinarySensorDescription(
        key="passenger_locked",
        translation_key="passenger_locked",
        name="Puerta Delantera Derecha Bloqueo",
        device_class=BinarySensorDeviceClass.LOCK,
        icon_on="mdi:car-door-lock",
        icon_off="mdi:car-door-lock-open",
        value_fn=lambda data: data.passenger_locked,
    ),
    DeepalBinarySensorDescription(
        key="left_front_tire_alarm",
        translation_key="left_front_tire_alarm",
        name="Alarma neumático delantero izquierdo",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon_on="mdi:car-tire-alert",
        icon_off="mdi:tire",
        value_fn=lambda data: data.left_front_tire_alarm,
    ),
    DeepalBinarySensorDescription(
        key="right_front_tire_alarm",
        translation_key="right_front_tire_alarm",
        name="Alarma neumático delantero derecho",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon_on="mdi:car-tire-alert",
        icon_off="mdi:tire",
        value_fn=lambda data: data.right_front_tire_alarm,
    ),
    DeepalBinarySensorDescription(
        key="left_rear_tire_alarm",
        translation_key="left_rear_tire_alarm",
        name="Alarma neumático trasero izquierdo",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon_on="mdi:car-tire-alert",
        icon_off="mdi:tire",
        value_fn=lambda data: data.left_rear_tire_alarm,
    ),
    DeepalBinarySensorDescription(
        key="right_rear_tire_alarm",
        translation_key="right_rear_tire_alarm",
        name="Alarma neumático trasero derecho",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon_on="mdi:car-tire-alert",
        icon_off="mdi:tire",
        value_fn=lambda data: data.right_rear_tire_alarm,
    ),
    DeepalBinarySensorDescription(
        key="high_beam",
        translation_key="high_beam",
        name="Luz de carretera",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon_on="dec:car-light-full-on",
        icon_off="dec:car-light-full-off",
        value_fn=lambda data: data.high_beam,
    ),
    DeepalBinarySensorDescription(
        key="low_beam",
        translation_key="low_beam",
        name="Luz de cruce",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon_on="dec:car-light-dimmed-on",
        icon_off="dec:car-light-dimmed-off",
        value_fn=lambda data: data.low_beam,
    ),
    DeepalBinarySensorDescription(
        key="position_lamp",
        translation_key="position_lamp",
        name="Luz de posición",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon_on="dec:car-light-parking-on",
        icon_off="dec:car-light-parking-off",
        value_fn=lambda data: data.position_lamp,
    ),
    DeepalBinarySensorDescription(
        key="left_indicator",
        translation_key="left_indicator",
        name="Luz Intermitente Izquierdo",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon_on="dec:arrow-circle-left",
        icon_off="dec:arrow-circle-left-outline",
        value_fn=lambda data: data.left_indicator,
    ),
    DeepalBinarySensorDescription(
        key="right_indicator",
        translation_key="right_indicator",
        name="Luz Intermitente Derecho",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon_on="dec:arrow-circle-right",
        icon_off="dec:arrow-circle-right-outline",
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
        name="Climatizador - Estado",
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

