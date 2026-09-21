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
        key="mileage_yesterday",
        translation_key="mileage_yesterday",
        name="Kilometraje de ayer",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.mileage_yesterday_km,
    ),
    DeepalSensorDescription(
        key="ignition_cumulative_mileage",
        translation_key="ignition_cumulative_mileage",
        name="Kilometraje desde el encendido",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ignition_cumulative_mileage_km,
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
        key="remaining_charge_time",
        translation_key="remaining_charge_time",
        name="Tiempo de carga restante",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data: data.remaining_charge_minutes,
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
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.right_rear_tire_pressure,
    ),
    DeepalSensorDescription(
        key="left_front_tire_temperature",
        translation_key="left_front_tire_temperature",
        name="Temperatura neumático delantero izquierdo",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.left_front_tire_temperature_c,
    ),
    DeepalSensorDescription(
        key="right_front_tire_temperature",
        translation_key="right_front_tire_temperature",
        name="Temperatura neumático delantero derecho",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.right_front_tire_temperature_c,
    ),
    DeepalSensorDescription(
        key="left_rear_tire_temperature",
        translation_key="left_rear_tire_temperature",
        name="Temperatura neumático trasero izquierdo",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.left_rear_tire_temperature_c,
    ),
    DeepalSensorDescription(
        key="right_rear_tire_temperature",
        translation_key="right_rear_tire_temperature",
        name="Temperatura neumático trasero derecho",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.right_rear_tire_temperature_c,
    ),
    DeepalSensorDescription(
        key="fan_speed",
        translation_key="fan_speed",
        name="Velocidad del ventilador",
        icon="mdi:fan",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.fan_speed,
    ),
    DeepalSensorDescription(
        key="climate_target_temperature",
        translation_key="climate_target_temperature",
        name="Consigna de temperatura",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.climate_target_temperature_c,
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
