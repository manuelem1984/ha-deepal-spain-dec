"""Telemetry normalization for Deepal Spain DEC."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .models import DeepalTelemetry


def as_int(value: Any) -> int | None:
    """Convert a value to an integer."""
    if value is None:
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def as_float(value: Any) -> float | None:
    """Convert a value to a floating-point number."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value: Any) -> bool | None:
    """Convert a numeric Deepal state to a boolean."""
    parsed_value = as_int(value)

    if parsed_value is None:
        return None

    return parsed_value != 0


def first_value(
    parameters: dict[str, Any],
    *keys: str,
) -> Any:
    """Return the first available value from a list of keys."""
    for key in keys:
        value = parameters.get(key)

        if value is not None:
            return value

    return None


def parse_datetime(value: Any) -> datetime | None:
    """Convert a Deepal timestamp into a UTC datetime."""
    if not isinstance(value, str) or not value:
        return None

    try:
        parsed_value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if parsed_value.tzinfo is None:
        parsed_value = parsed_value.replace(tzinfo=UTC)

    return parsed_value.astimezone(UTC)


def parse_remaining_charge_time(value: Any) -> int | None:
    """Normalize the remaining charge time."""
    parsed_value = as_int(value)

    if parsed_value in (None, 8191):
        return None

    return parsed_value


def normalize_humidity(value: Any) -> float | None:
    """Normalize cabin humidity reported in tenths of a percent."""
    parsed_value = as_float(value)

    if parsed_value is None:
        return None

    humidity = parsed_value / 10

    if not 0 <= humidity <= 100:
        return None

    return humidity


def parameters_to_telemetry(
    parameters: dict[str, Any],
) -> DeepalTelemetry:
    """Convert raw Deepal MQTT parameters into normalized telemetry."""
    return DeepalTelemetry(
        # Battery
        battery_level=as_int(
            first_value(
                parameters,
                "soc",
                "socDsp",
                "remainPower",
            )
        ),
        estimated_range_km=as_int(
            first_value(
                parameters,
                "remainedPowerMile",
                "totalResidualMileage",
            )
        ),

        # Vehicle
        connected=True,
        engine_on=as_bool(parameters.get("engineStatus")),
        mileage_km=as_float(parameters.get("totalOdometer")),
        speed_kmh=as_float(
            first_value(
                parameters,
                "vehicleSpeed",
                "speed",
            )
        ),
        last_update=parse_datetime(
            first_value(
                parameters,
                "latestDate",
                "lastUpdatedAt",
            )
        ),

        # Charging
        charging=as_bool(parameters.get("ChrgSts")),
        charge_current=as_float(
            first_value(
                parameters,
                "BattACChrgInCurr",
                "BattDCChrgInCurr",
                "battACChrgInCurr",
                "battDCChrgInCurr",
            )
        ),
        remaining_charge_minutes=parse_remaining_charge_time(
            parameters.get("chargDeltMins")
        ),

        # Climate
        inside_temperature_c=as_float(
            parameters.get("vehicleTemperature")
        ),
        outside_temperature_c=as_float(
            first_value(
                parameters,
                "outsideTemperature",
                "externalTemperature",
            )
        ),
        cabin_humidity_percent=normalize_humidity(
            parameters.get("innerHumidity")
        ),

        # Doors
        front_left_door=as_bool(parameters.get("driverDoor")),
        front_right_door=as_bool(
            parameters.get("passengerDoor")
        ),
        rear_left_door=as_bool(parameters.get("leftRearDoor")),
        rear_right_door=as_bool(parameters.get("rightRearDoor")),
        trunk_open=as_bool(parameters.get("trunk")),

        # Locks
        driver_locked=as_bool(parameters.get("driverDoorLock")),
        passenger_locked=as_bool(
            parameters.get("passengerDoorLock")
        ),

        # Windows
        front_left_window=as_bool(
            parameters.get("diverWindow")
        ),
        front_right_window=as_bool(
            parameters.get("passengerWindow")
        ),
        rear_left_window=as_bool(
            parameters.get("leftRearWindow")
        ),
        rear_right_window=as_bool(
            parameters.get("rightRearWindow")
        ),

        # Tyres
        left_front_tire_pressure=as_float(
            parameters.get("lfTyrePressure")
        ),
        right_front_tire_pressure=as_float(
            parameters.get("rfTyrePressure")
        ),
        left_rear_tire_pressure=as_float(
            parameters.get("lrTyrePressure")
        ),
        right_rear_tire_pressure=as_float(
            parameters.get("rrTyrePressure")
        ),

        # Lights
        high_beam=as_bool(parameters.get("highBeam")),
        low_beam=as_bool(parameters.get("lowBeam")),
        position_lamp=as_bool(parameters.get("positionLamp")),
        left_indicator=as_bool(
            parameters.get("turnLndicatorLeft")
        ),
        right_indicator=as_bool(
            parameters.get("turnLndicatorRight")
        ),
    )
