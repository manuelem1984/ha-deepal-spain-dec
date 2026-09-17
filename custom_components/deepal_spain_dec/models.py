"""Data models for the Deepal Spain DEC integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class DeepalSession:
    """Authentication session returned by the Deepal Spain API."""

    access_token: str
    refresh_token: str | None = None
    cac_token: str | None = None
    user_id: str | None = None
    ca_user_id: str | None = None
    cac_user_id: str | None = None


@dataclass(slots=True)
class DeepalVehicle:
    """Vehicle registered in the Deepal account."""

    vehicle_id: str
    vin: str | None = None
    model_name: str | None = None
    protocol_type: str | None = None
    image_url: str | None = None


@dataclass(slots=True)
class DeepalTelemetry:
    """Normalized telemetry for a Deepal vehicle."""

    updated_at: datetime | None = None

    battery_level: int | None = None
    estimated_range_km: int | None = None
    total_mileage_km: float | None = None
    speed_kmh: float | None = None

    vehicle_connected: bool | None = None
    engine_on: bool | None = None

    inside_temperature_c: float | None = None
    outside_temperature_c: float | None = None
    cabin_humidity_percent: float | None = None

    charging: bool | None = None
    charge_cable_connected: bool | None = None
    remaining_charge_minutes: int | None = None
    charge_current_a: float | None = None

    doors_open: dict[str, bool | None] = field(default_factory=dict)
    doors_locked: dict[str, bool | None] = field(default_factory=dict)
    windows_open: dict[str, bool | None] = field(default_factory=dict)

    tire_pressure_kpa: dict[str, float | None] = field(default_factory=dict)

    high_beam_on: bool | None = None
    low_beam_on: bool | None = None
    position_lamp_on: bool | None = None
    left_turn_signal_on: bool | None = None
    right_turn_signal_on: bool | None = None

    raw: dict = field(default_factory=dict)
