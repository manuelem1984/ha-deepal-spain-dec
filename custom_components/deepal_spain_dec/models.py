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
    speed_kmh: float | None = None

    last_update: datetime | None = None

    # Charging
    charging: bool | None = None

    charge_current: float | None = None

    remaining_charge_minutes: int | None = None

    # Climate
    inside_temperature_c: float | None = None
    outside_temperature_c: float | None = None

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

    # Windows
    front_left_window: bool | None = None
    front_right_window: bool | None = None

    rear_left_window: bool | None = None
    rear_right_window: bool | None = None

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
