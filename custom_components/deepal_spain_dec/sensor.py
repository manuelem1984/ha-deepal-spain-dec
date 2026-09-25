"""Sensor platform for Deepal Spain DEC."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
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
class DeepalSensorDescription(
    SensorEntityDescription
):
    """Describe a Deepal Spain sensor."""

    value_fn: Callable[
        [DeepalTelemetry],
        Any,
    ]

    # Optional per-value icon override — e.g. a different plug icon
    # for each possible state of an enum sensor. Keyed by the exact
    # string value_fn returns; falls back to `icon` / the
    # device_class default when the current value isn't a key here
    # (including when it's None).
    icon_map: dict[str, str] | None = None


# Possible states of the "Carga - Estado" sensor below — also its
# device_class=ENUM options, and the keys translated in
# strings.json/translations/*.json (entity.sensor.charge_status.state).
CHARGE_STATUS_DISCONNECTED = "disconnected"
CHARGE_STATUS_CONNECTED_AC = "connected_ac"
CHARGE_STATUS_CONNECTED_DC = "connected_dc"
CHARGE_STATUS_CHARGING_AC = "charging_ac"
CHARGE_STATUS_CHARGING_DC = "charging_dc"

CHARGE_STATUS_OPTIONS = [
    CHARGE_STATUS_DISCONNECTED,
    CHARGE_STATUS_CONNECTED_AC,
    CHARGE_STATUS_CONNECTED_DC,
    CHARGE_STATUS_CHARGING_AC,
    CHARGE_STATUS_CHARGING_DC,
]

CHARGE_STATUS_ICONS = {
    CHARGE_STATUS_DISCONNECTED: "mdi:power-plug-off",
    CHARGE_STATUS_CONNECTED_AC: "mdi:ev-plug-type2",
    CHARGE_STATUS_CONNECTED_DC: "mdi:ev-plug-ccs2",
    CHARGE_STATUS_CHARGING_AC: "mdi:lightning-bolt-outline",
    CHARGE_STATUS_CHARGING_DC: "mdi:flash-outline",
}


def _charge_status(data: DeepalTelemetry) -> str | None:
    """Combine "Carga", "Conector AC" and "Conector DC" into one state.

    Evaluated in this exact order, matching the user's own
    specification:
    1. Neither connector plugged in and not charging -> disconnected.
    2. AC plugged in, not charging -> connected_ac.
    3. DC plugged in, not charging -> connected_dc.
    4. AC plugged in, charging -> charging_ac.
    5. DC plugged in, charging -> charging_dc.

    Returns None (shown as "unknown") rather than guessing a label
    when any of the three underlying values isn't known yet, or when
    none of the five cases above match (e.g. charging without either
    connector reporting plugged in — physically shouldn't happen, but
    telemetry can lag).
    """
    ac = data.ac_charge_connector_connected
    dc = data.dc_charge_connector_connected
    charging = data.charging

    if ac is None or dc is None or charging is None:
        return None

    if not ac and not dc and not charging:
        return CHARGE_STATUS_DISCONNECTED

    if ac and not charging:
        return CHARGE_STATUS_CONNECTED_AC

    if dc and not charging:
        return CHARGE_STATUS_CONNECTED_DC

    if ac and charging:
        return CHARGE_STATUS_CHARGING_AC

    if dc and charging:
        return CHARGE_STATUS_CHARGING_DC

    return None


SENSOR_DESCRIPTIONS: tuple[
    DeepalSensorDescription,
    ...,
] = (
    DeepalSensorDescription(
        key="battery_level",
        translation_key="battery_level",
        name="Batería",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.battery_level,
    ),
    DeepalSensorDescription(
        key="estimated_range",
        translation_key="estimated_range",
        name="Autonomía estimada",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.estimated_range_km,
    ),
    DeepalSensorDescription(
        key="total_mileage",
        translation_key="total_mileage",
        name="Kilometraje total",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.mileage_km,
    ),
    DeepalSensorDescription(
        key="last_update",
        translation_key="last_update",
        name="Última actualización",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.last_update,
    ),
    DeepalSensorDescription(
        key="charge_current",
        translation_key="charge_current",
        name="Corriente de carga",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.charge_current,
    ),
    DeepalSensorDescription(
        key="ac_charge_current",
        translation_key="ac_charge_current",
        name="Corriente de carga AC",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
        value_fn=lambda data: data.ac_charge_current,
    ),
    DeepalSensorDescription(
        key="dc_charge_current",
        translation_key="dc_charge_current",
        name="Corriente de carga DC",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        value_fn=lambda data: data.dc_charge_current,
    ),
    DeepalSensorDescription(
        key="remaining_charge_time",
        translation_key="remaining_charge_time",
        name="Tiempo de carga restante",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.remaining_charge_minutes,
    ),
    DeepalSensorDescription(
        key="charge_status",
        translation_key="charge_status",
        name="Carga - Estado",
        device_class=SensorDeviceClass.ENUM,
        options=CHARGE_STATUS_OPTIONS,
        icon_map=CHARGE_STATUS_ICONS,
        value_fn=_charge_status,
    ),
    DeepalSensorDescription(
        key="inside_temperature",
        translation_key="inside_temperature",
        name="Temperatura interior",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.inside_temperature_c,
    ),
    DeepalSensorDescription(
        key="cabin_humidity",
        translation_key="cabin_humidity",
        name="Humedad interior",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.cabin_humidity_percent,
    ),
    DeepalSensorDescription(
        key="left_front_tire_pressure",
        translation_key="left_front_tire_pressure",
        name="Presión neumático delantero izquierdo",
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.left_front_tire_pressure,
    ),
    DeepalSensorDescription(
        key="right_front_tire_pressure",
        translation_key="right_front_tire_pressure",
        name="Presión neumático delantero derecho",
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.right_front_tire_pressure,
    ),
    DeepalSensorDescription(
        key="left_rear_tire_pressure",
        translation_key="left_rear_tire_pressure",
        name="Presión neumático trasero izquierdo",
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.left_rear_tire_pressure,
    ),
    DeepalSensorDescription(
        key="right_rear_tire_pressure",
        translation_key="right_rear_tire_pressure",
        name="Presión neumático trasero derecho",
        device_class=SensorDeviceClass.PRESSURE,
        icon="mdi:car-tire-alert",
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.right_rear_tire_pressure,
    ),
    DeepalSensorDescription(
        key="fan_speed",
        translation_key="fan_speed",
        name="Climatizador - Ventilador",
        icon="mdi:fan",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.fan_speed,
    ),
    DeepalSensorDescription(
        key="climate_target_temperature",
        translation_key="climate_target_temperature",
        name="Climatizador - Temperatura",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.climate_target_temperature_c,
    ),
    # Raw integer code from `powerStatusFeedBack`. The meaning of each
    # value (off / accessory / on / ready...) is not mapped yet, so it
    # stays a plain diagnostic number instead of guessing labels. See
    # docs/telemetry-parameters.md.
    DeepalSensorDescription(
        key="power_status",
        translation_key="power_status",
        name="Estado de alimentación",
        icon="mdi:car-cog",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.power_status,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deepal Spain sensors."""
    coordinator: DeepalSpainCoordinator = (
        hass.data[DOMAIN][entry.entry_id]
    )

    async_add_entities(
        DeepalSpainSensor(
            coordinator,
            description,
        )
        for description in SENSOR_DESCRIPTIONS
    )


class DeepalSpainSensor(
    DeepalSpainEntity,
    SensorEntity,
):
    """Representation of a Deepal Spain sensor."""

    entity_description: DeepalSensorDescription

    def __init__(
        self,
        coordinator: DeepalSpainCoordinator,
        description: DeepalSensorDescription,
    ) -> None:
        """Initialize a Deepal Spain sensor."""
        super().__init__(
            coordinator,
            description.key,
        )

        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        data = self.coordinator.data

        if data is None:
            return None

        return self.entity_description.value_fn(data)

    @property
    def icon(self) -> str | None:
        """Return a per-value icon when the description defines one."""
        icon_map = self.entity_description.icon_map

        if not icon_map:
            return self.entity_description.icon

        value = self.native_value

        if value not in icon_map:
            return self.entity_description.icon

        return icon_map[value]
