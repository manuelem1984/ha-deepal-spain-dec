"""Telemetry normalization for Deepal Spain DEC."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .models import DeepalTelemetry


# Every raw vehicle key that parameters_to_telemetry() below reads,
# grouped the same way as the DeepalTelemetry fields they feed.
# diagnostics.py uses this to tell mapped fields apart from ones the
# vehicle sends but no entity uses yet, without duplicating the list.
MAPPED_KEYS: frozenset[str] = frozenset(
    {
        # Battery
        "soc",
        "socDsp",
        "remainPower",
        "remainedPowerMile",
        "totalResidualMileage",
        # Vehicle
        "engineStatus",
        "powerStatusFeedBack",
        "totalOdometer",
        "latestDate",
        "lastUpdatedAt",
        # Charging
        "ChrgSts",
        "BattACChrgInCurr",
        "BattDCChrgInCurr",
        "battACChrgInCurr",
        "battDCChrgInCurr",
        "chargDeltMins",
        "acChargeGunConnectionState",
        "dcChargeGunConnectionState",
        # Climate
        "vehicleTemperature",
        "innerHumidity",
        # Doors
        "driverDoor",
        "passengerDoor",
        "leftRearDoor",
        "rightRearDoor",
        "trunk",
        # Windows
        "diverWindow",
        "passengerWindow",
        "leftRearWindow",
        "rightRearWindow",
        # Locks
        "driverDoorLock",
        "passengerDoorLock",
        # Tyres
        "lfTyrePressure",
        "rfTyrePressure",
        "lrTyrePressure",
        "rrTyrePressure",
        "lfPressureWarning",
        "rfPressureWarning",
        "lrPressureWarning",
        "rrPressureWarning",
        # Lights
        "highBeam",
        "lowBeam",
        "positionLamp",
        "turnLndicatorLeft",
        "turnLndicatorRight",
        # Body
        "hoodStatus",
        # Climate control
        "airStatus",
        "airConditioningHairRatings",
        "airConditioningSetTemperature",
        "driverSeatHeatStatus",
        "passengerSeatHeatStatus",
        "driverSeatAirStatus",
        "passengerSeatAirStatus",
        "steeringWheelHeating",
        "frontDefrostStatus",
    }
)


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


def as_seat_level(value: Any) -> int | None:
    """Convert a raw 0-6 seat heat/vent value to a 0-3 level.

    Deepal's own API reports these in a 0-6 "gear" scale; the level
    shown in the app (and here) is that value divided by two. Scale
    cross-checked against an independent reference implementation for
    this vehicle class, not yet confirmed against this specific vehicle.
    """
    parsed_value = as_int(value)

    if parsed_value is None:
        return None

    return parsed_value // 2


def as_charge_connector_connected(value: Any) -> bool | None:
    """Return whether a charge connector state means a gun is plugged in.

    The raw value is *not* a plain boolean — 0 **and** 1 both mean
    "not connected"; only 2 or higher means connected (a charging AC
    gun was observed reporting 3). A plain as_bool() would treat 1 as
    "connected", which is wrong — confirmed on the real car, which
    reported 1 while genuinely unplugged ("Conector AC: Enchufado"
    was shown by mistake before this helper existed). The same
    threshold is used by an independent reference implementation
    that checked 0 against a parked, unplugged car.
    """
    parsed_value = as_int(value)

    if parsed_value is None:
        return None

    return parsed_value not in (0, 1)


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


def any_door_open(data: DeepalTelemetry) -> bool | None:
    """Return whether any door or the trunk is open.

    Aggregates the four doors plus the trunk (the hood is left out on
    purpose: it is not a way into the cabin). True as soon as one of
    them reports open; False only when at least one is known and none
    is open; None when none of the five is known yet.
    """
    values = (
        data.front_left_door,
        data.front_right_door,
        data.rear_left_door,
        data.rear_right_door,
        data.trunk_open,
    )

    if all(value is None for value in values):
        return None

    return any(value is True for value in values)


def any_door_unlocked(data: DeepalTelemetry) -> bool | None:
    """Return whether the car is unlocked (either front lock open).

    Follows exactly the same convention as the existing per-door
    "Bloqueo" sensors, so all three always agree: `driver_locked` /
    `passenger_locked` hold the raw lock flag as a boolean (non-zero
    raw value -> True), and a True `is_on` is shown by Home
    Assistant's LOCK device class as "unlocked". Reference material
    for this backend states that raw 0 means locked; that has not
    been re-checked on the real car yet (see
    docs/telemetry-parameters.md). The S05 reports only the two front
    locks; the rear doors follow the central locking.

    None when neither front lock is known yet.
    """
    values = (data.driver_locked, data.passenger_locked)

    if all(value is None for value in values):
        return None

    return any(value is True for value in values)


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
        power_status=as_int(parameters.get("powerStatusFeedBack")),
        mileage_km=as_float(parameters.get("totalOdometer")),
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
        ac_charge_current=as_float(
            first_value(
                parameters,
                "BattACChrgInCurr",
                "battACChrgInCurr",
            )
        ),
        dc_charge_current=as_float(
            first_value(
                parameters,
                "BattDCChrgInCurr",
                "battDCChrgInCurr",
            )
        ),
        remaining_charge_minutes=parse_remaining_charge_time(
            parameters.get("chargDeltMins")
        ),
        ac_charge_connector_connected=as_charge_connector_connected(
            parameters.get("acChargeGunConnectionState")
        ),
        dc_charge_connector_connected=as_charge_connector_connected(
            parameters.get("dcChargeGunConnectionState")
        ),

        # Climate
        inside_temperature_c=as_float(
            parameters.get("vehicleTemperature")
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

        # Windows
        front_left_window_open=as_bool(parameters.get("diverWindow")),
        front_right_window_open=as_bool(
            parameters.get("passengerWindow")
        ),
        rear_left_window_open=as_bool(
            parameters.get("leftRearWindow")
        ),
        rear_right_window_open=as_bool(
            parameters.get("rightRearWindow")
        ),

        # Locks
        driver_locked=as_bool(parameters.get("driverDoorLock")),
        passenger_locked=as_bool(
            parameters.get("passengerDoorLock")
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
        left_front_tire_alarm=as_bool(
            parameters.get("lfPressureWarning")
        ),
        right_front_tire_alarm=as_bool(
            parameters.get("rfPressureWarning")
        ),
        left_rear_tire_alarm=as_bool(
            parameters.get("lrPressureWarning")
        ),
        right_rear_tire_alarm=as_bool(
            parameters.get("rrPressureWarning")
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

        # Body
        hood_open=as_bool(parameters.get("hoodStatus")),

        # Climate control
        climate_on=as_bool(parameters.get("airStatus")),
        fan_speed=as_int(
            parameters.get("airConditioningHairRatings")
        ),
        climate_target_temperature_c=as_float(
            parameters.get("airConditioningSetTemperature")
        ),
        # Fallback only — confirmed unreliable for these four over
        # MQTT (comparing two real captures a few minutes apart, with
        # the vehicle's actual state changed and confirmed via the
        # official app in between, these MQTT fields did not follow).
        # coordinator._async_overlay_condition() replaces them with a
        # more reliable source when that call succeeds; this MQTT
        # value is only what remains if it doesn't.
        driver_seat_heat_level=as_seat_level(
            parameters.get("driverSeatHeatStatus")
        ),
        passenger_seat_heat_level=as_seat_level(
            parameters.get("passengerSeatHeatStatus")
        ),
        driver_seat_vent_level=as_seat_level(
            parameters.get("driverSeatAirStatus")
        ),
        passenger_seat_vent_level=as_seat_level(
            parameters.get("passengerSeatAirStatus")
        ),
        steering_wheel_heat_on=as_bool(
            parameters.get("steeringWheelHeating")
        ),
        front_defrost_on=as_bool(
            parameters.get("frontDefrostStatus")
        ),
    )


def parse_condition_overlay(raw: dict[str, Any]) -> dict[str, Any]:
    """Extract the handful of fields this integration overlays.

    Takes the response of api.get_condition_overlay() — nested by
    category (e.g. raw["seat"]["leftFront"]["heatStatus"]), a totally
    different shape from the flat MQTT payload parameters_to_telemetry()
    reads. Returns a {field_name: value} dict suitable for
    dataclasses.replace(telemetry, **result) — only the keys that
    could actually be parsed, so a partial or malformed response
    overlays only what it safely can rather than clearing fields with
    None.

    Field names and the fact that this endpoint is reliable where the
    equivalent MQTT fields are not were cross-checked against an
    independent reference implementation; not yet confirmed end-to-end
    against this vehicle (see docs/remote-control.md).
    """
    seat = raw.get("seat")
    seat = seat if isinstance(seat, dict) else {}

    hvac = raw.get("hvac")
    hvac = hvac if isinstance(hvac, dict) else {}

    vehicle_status = raw.get("vehicleStatus")
    vehicle_status = (
        vehicle_status if isinstance(vehicle_status, dict) else {}
    )

    def _seat_field(position: str, *keys: str) -> int | None:
        data = seat.get(position)

        if not isinstance(data, dict):
            return None

        for key in keys:
            level = as_int(data.get(key))
            if level is not None:
                return level if level > 0 else 0

        return None

    result: dict[str, Any] = {}

    driver_heat = _seat_field("leftFront", "heatStatus", "level")
    if driver_heat is not None:
        result["driver_seat_heat_level"] = driver_heat

    passenger_heat = _seat_field("rightFront", "heatStatus", "level")
    if passenger_heat is not None:
        result["passenger_seat_heat_level"] = passenger_heat

    driver_vent = _seat_field("leftFront", "ventStatus")
    if driver_vent is not None:
        result["driver_seat_vent_level"] = driver_vent

    passenger_vent = _seat_field("rightFront", "ventStatus")
    if passenger_vent is not None:
        result["passenger_seat_vent_level"] = passenger_vent

    steering_heater = as_int(vehicle_status.get("steeringWheelHeater"))
    if steering_heater is not None:
        result["steering_wheel_heat_on"] = steering_heater != 0

    defrost = as_int(hvac.get("defrostStatus"))
    if defrost is not None:
        result["front_defrost_on"] = defrost != 0

    return result
