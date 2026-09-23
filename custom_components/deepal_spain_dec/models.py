"""Data models for Deepal Spain DEC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------


@dataclass(slots=True)
class DeepalSession:
    """Authenticated Deepal session."""

    access_token: str
    refresh_token: str | None = None

    cac_token: str | None = None

    user_id: str | None = None
    ca_user_id: str | None = None
    cac_user_id: str | None = None


# ------------------------------------------------------------------
# Vehicle
# ------------------------------------------------------------------


@dataclass(slots=True)
class DeepalVehicle:
    """Vehicle information."""

    vehicle_id: str

    vin: str | None = None
    model_name: str | None = None

    image_url: str | None = None

    mqtt_enabled: bool = False


# ------------------------------------------------------------------
# Telemetry
# ------------------------------------------------------------------


@dataclass(slots=True)
class DeepalTelemetry:
    """Normalized telemetry exposed to Home Assistant."""

    # Battery
    battery_level: int | None = None
    estimated_range_km: int | None = None

    # Vehicle
    connected: bool | None = None
    engine_on: bool | None = None

    mileage_km: float | None = None

    last_update: datetime | None = None

    # Charging
    charging: bool | None = None

    charge_current: float | None = None

    remaining_charge_minutes: int | None = None

    # Climate
    inside_temperature_c: float | None = None

    cabin_humidity_percent: float | None = None

    # Doors
    front_left_door: bool | None = None
    front_right_door: bool | None = None

    rear_left_door: bool | None = None
    rear_right_door: bool | None = None

    trunk_open: bool | None = None

    # Locks
    driver_locked: bool | None = None
    passenger_locked: bool | None = None

    # Tyres
    left_front_tire_pressure: float | None = None
    right_front_tire_pressure: float | None = None

    left_rear_tire_pressure: float | None = None
    right_rear_tire_pressure: float | None = None

    # Lights
    high_beam: bool | None = None
    low_beam: bool | None = None

    position_lamp: bool | None = None

    left_indicator: bool | None = None
    right_indicator: bool | None = None

    # Body
    hood_open: bool | None = None

    # Climate control
    climate_on: bool | None = None
    fan_speed: int | None = None
    climate_target_temperature_c: float | None = None

    # Seat heating/ventilation level (0 = off, 1-3 = level) and
    # steering wheel heating / front defrost on-off. Field names and
    # scale (raw ÷ 2) cross-checked against ha-deepal-alternative's
    # own MQTT parsing for this exact vehicle class — not yet
    # confirmed against this specific vehicle. Remote control added
    # in v1.3.1b4 (see docs/remote-control.md); reading these was
    # added at the same time since a number/switch entity that always
    # shows "unknown" isn't very useful.
    driver_seat_heat_level: int | None = None
    passenger_seat_heat_level: int | None = None
    driver_seat_vent_level: int | None = None
    passenger_seat_vent_level: int | None = None
    steering_wheel_heat_on: bool | None = None
    front_defrost_on: bool | None = None
