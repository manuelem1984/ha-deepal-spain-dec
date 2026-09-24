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

    # Charging connector plugged in — AC (Type 2, slow/normal charging)
    # and DC (CCS2, fast charging) are reported separately.
    ac_charge_connector_connected: bool | None = None
    dc_charge_connector_connected: bool | None = None

    # Charging current split by connector type (amperes). The combined
    # `charge_current` above keeps its original behaviour (first value
    # available, AC or DC); these two report each side separately so a
    # dashboard can tell a wallbox session apart from a fast charger.
    ac_charge_current: float | None = None
    dc_charge_current: float | None = None

    # Raw power-mode feedback (`powerStatusFeedBack`). Integer code as
    # sent by the car; the meaning of each value has not been mapped
    # yet, so it is exposed as-is in a diagnostic sensor.
    power_status: int | None = None

    # Climate
    inside_temperature_c: float | None = None

    cabin_humidity_percent: float | None = None

    # Doors
    front_left_door: bool | None = None
    front_right_door: bool | None = None

    rear_left_door: bool | None = None
    rear_right_door: bool | None = None

    trunk_open: bool | None = None

    # Windows (True = open). Fed by `diverWindow` (sic — the car's own
    # typo), `passengerWindow`, `leftRearWindow` and `rightRearWindow`.
    front_left_window_open: bool | None = None
    front_right_window_open: bool | None = None

    rear_left_window_open: bool | None = None
    rear_right_window_open: bool | None = None

    # Locks
    driver_locked: bool | None = None
    passenger_locked: bool | None = None

    # Tyres
    left_front_tire_pressure: float | None = None
    right_front_tire_pressure: float | None = None

    left_rear_tire_pressure: float | None = None
    right_rear_tire_pressure: float | None = None

    # Tyre pressure warnings (True = the car flags a problem on that
    # tyre). Fed by `lfPressureWarning`, `rfPressureWarning`,
    # `lrPressureWarning` and `rrPressureWarning`.
    left_front_tire_alarm: bool | None = None
    right_front_tire_alarm: bool | None = None

    left_rear_tire_alarm: bool | None = None
    right_rear_tire_alarm: bool | None = None

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
    # scale (raw ÷ 2) cross-checked against an independent reference
    # implementation for this exact vehicle class — not yet
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
