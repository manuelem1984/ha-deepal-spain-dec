"""Unit tests for telemetry.py normalization helpers.

Pure-function tests: no network, no Home Assistant, no vehicle required.
They run in a couple of seconds and are wired into CI (.github/workflows/lint.yaml).

`realistic_payload` below reuses the real field *names* the Deepal S05 sent in
the MQTT capture documented in docs/telemetry-parameters.md. Values for fields
already confirmed against the real car (battery, doors, locks, tyres, lights,
charging) are realistic; values for fields still pending confirmation (see
that document's "Candidatas prioritarias" section) are plausible placeholders
and are NOT asserted on here — only the already-implemented mapping is tested.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from custom_components.deepal_spain_dec import telemetry
from custom_components.deepal_spain_dec.models import DeepalTelemetry


# ---------------------------------------------------------------------------
# as_int
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (10, 10),
        ("10", 10),
        (10.7, 10),  # truncates towards zero, like int(float(value))
        ("10.7", 10),
        (0, 0),
        (None, None),
        ("not-a-number", None),
        ([], None),
    ],
)
def test_as_int(value, expected):
    assert telemetry.as_int(value) == expected


# ---------------------------------------------------------------------------
# as_float
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (10, 10.0),
        ("10.5", 10.5),
        (0, 0.0),
        (None, None),
        ("not-a-number", None),
    ],
)
def test_as_float(value, expected):
    assert telemetry.as_float(value) == expected


# ---------------------------------------------------------------------------
# as_bool
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, False),
        (1, True),
        (2, True),  # any non-zero value counts as True
        ("0", False),
        ("1", True),
        (None, None),
        ("not-a-number", None),
    ],
)
def test_as_bool(value, expected):
    assert telemetry.as_bool(value) == expected


# ---------------------------------------------------------------------------
# first_value
# ---------------------------------------------------------------------------


def test_first_value_returns_first_present_key():
    parameters = {"b": 2, "c": 3}
    assert telemetry.first_value(parameters, "a", "b", "c") == 2


def test_first_value_skips_none_values():
    parameters = {"a": None, "b": 5}
    assert telemetry.first_value(parameters, "a", "b") == 5


def test_first_value_returns_none_when_nothing_present():
    assert telemetry.first_value({}, "a", "b") is None


# ---------------------------------------------------------------------------
# parse_datetime
# ---------------------------------------------------------------------------


def test_parse_datetime_with_z_suffix():
    result = telemetry.parse_datetime("2026-09-18T00:48:36Z")
    assert result == datetime(2026, 9, 18, 0, 48, 36, tzinfo=UTC)


def test_parse_datetime_with_explicit_offset():
    result = telemetry.parse_datetime("2026-09-18T02:48:36+02:00")
    assert result == datetime(2026, 9, 18, 0, 48, 36, tzinfo=UTC)


@pytest.mark.parametrize("value", [None, "", "not-a-date", 12345])
def test_parse_datetime_invalid_input(value):
    assert telemetry.parse_datetime(value) is None


# ---------------------------------------------------------------------------
# parse_remaining_charge_time
# ---------------------------------------------------------------------------


def test_parse_remaining_charge_time_normal_value():
    assert telemetry.parse_remaining_charge_time(45) == 45


def test_parse_remaining_charge_time_sentinel_is_none():
    # 8191 is the "not charging / no data" sentinel the vehicle sends.
    assert telemetry.parse_remaining_charge_time(8191) is None


def test_parse_remaining_charge_time_none_is_none():
    assert telemetry.parse_remaining_charge_time(None) is None


# ---------------------------------------------------------------------------
# normalize_humidity
# ---------------------------------------------------------------------------


def test_normalize_humidity_converts_tenths_of_percent():
    # Real capture showed innerHumidity=69 -> 6.9 %
    assert telemetry.normalize_humidity(69) == 6.9


def test_normalize_humidity_rejects_out_of_range():
    assert telemetry.normalize_humidity(2000) is None  # would be 200 %


def test_normalize_humidity_none_is_none():
    assert telemetry.normalize_humidity(None) is None


# ---------------------------------------------------------------------------
# parameters_to_telemetry — full mapping
# ---------------------------------------------------------------------------


@pytest.fixture
def realistic_payload() -> dict:
    """A payload shaped like the real MQTT capture from the Deepal S05."""
    return {
        # Battery
        "soc": 38,
        "socDsp": 38,
        "remainPower": 38,
        "remainedPowerMile": 185,
        "totalResidualMileage": 185,
        # Vehicle
        "engineStatus": 0,
        "totalOdometer": 12345.6,
        "totalMeterYesterday": 42.3,
        "igniteCumulativeMileage": 5.7,
        "latestDate": "2026-09-18T00:48:36Z",
        # Charging
        "ChrgSts": 0,
        "BattACChrgInCurr": 0,
        "BattDCChrgInCurr": 0,
        "chargDeltMins": 8191,
        # Climate
        "vehicleTemperature": 24.0,
        "innerHumidity": 69,
        # Doors
        "driverDoor": 0,
        "passengerDoor": 0,
        "leftRearDoor": 0,
        "rightRearDoor": 0,
        "trunk": 0,
        # Locks
        "driverDoorLock": 1,
        "passengerDoorLock": 1,
        # Tyres
        "lfTyrePressure": 230,
        "rfTyrePressure": 230,
        "lrTyrePressure": 225,
        "rrTyrePressure": 225,
        # Tyre temperature — field names cross-checked against another
        # open-source Deepal integration (see docs/telemetry-parameters.md),
        # not yet confirmed against this vehicle.
        "leftFrontTireTemperature": 28.5,
        "rightFrontTireTemperature": 28.0,
        "leftRearTireTemperature": 27.5,
        "rightRearTireTemperature": 27.0,
        # Lights
        "highBeam": 0,
        "lowBeam": 0,
        "positionLamp": 0,
        "turnLndicatorLeft": 0,
        "turnLndicatorRight": 0,
        # Body / climate control (confirmed 2026-09-18)
        "hoodStatus": "1",
        "airStatus": 1,
        "airConditioningHairRatings": 2,
        "airConditioningSetTemperature": 22.5,
        # Fields the vehicle sends but the integration deliberately
        # does not map (see docs/telemetry-parameters.md):
        # - diverWindow/passengerWindow/leftRearWindow/rightRearWindow
        #   duplicated front_left_door/etc.; removed in v1.2.0 to avoid
        #   two entities for the same physical door.
        # - *WindowDegree fields turned out to report movement
        #   acceleration while the window is moving, not its resting
        #   position — not useful as a Home Assistant entity.
        "diverWindow": 0,
        "passengerWindow": 0,
        "leftRearWindow": 0,
        "rightRearWindow": 0,
        "leftAnteriorWindowDegree": "0",
        "skyWindowDegree": 0,
    }


def test_parameters_to_telemetry_maps_known_fields(realistic_payload):
    result = telemetry.parameters_to_telemetry(realistic_payload)

    assert isinstance(result, DeepalTelemetry)
    assert result.battery_level == 38
    assert result.estimated_range_km == 185
    assert result.connected is True
    assert result.engine_on is False
    assert result.mileage_km == 12345.6
    assert result.mileage_yesterday_km == 42.3
    assert result.ignition_cumulative_mileage_km == 5.7
    assert result.last_update == datetime(2026, 9, 18, 0, 48, 36, tzinfo=UTC)
    assert result.charging is False
    assert result.remaining_charge_minutes is None  # 8191 sentinel
    assert result.inside_temperature_c == 24.0
    assert result.cabin_humidity_percent == 6.9
    assert result.front_left_door is False
    assert result.driver_locked is True
    assert result.left_front_tire_pressure == 230
    assert result.left_front_tire_temperature_c == 28.5
    assert result.right_rear_tire_temperature_c == 27.0
    assert result.high_beam is False
    # Confirmed against the real vehicle on 2026-09-18.
    assert result.hood_open is True
    assert result.climate_on is True
    assert result.fan_speed == 2
    assert result.climate_target_temperature_c == 22.5


def test_telemetry_has_no_removed_fields():
    # Removed in v1.2.0 — speed and outside temperature are never
    # sent by the real vehicle (see docs/telemetry-parameters.md,
    # "Buscadas pero nunca recibidas"); front_left_window/etc.
    # duplicated front_left_door/etc.; the *WindowDegree fields report
    # movement acceleration, not window position. Keeping this test
    # ensures nobody re-adds them without re-reading why they were
    # taken out.
    removed_fields = {
        "speed_kmh",
        "outside_temperature_c",
        "front_left_window",
        "front_right_window",
        "rear_left_window",
        "rear_right_window",
        "front_left_window_percent",
        "front_right_window_percent",
        "rear_left_window_percent",
        "rear_right_window_percent",
    }
    existing_fields = {
        field.name for field in dataclasses.fields(DeepalTelemetry)
    }
    assert removed_fields.isdisjoint(existing_fields)


def test_parameters_to_telemetry_prefers_first_available_battery_key():
    payload = {"remainPower": 50}  # soc / socDsp absent
    result = telemetry.parameters_to_telemetry(payload)
    assert result.battery_level == 50


def test_parameters_to_telemetry_handles_empty_payload():
    result = telemetry.parameters_to_telemetry({})
    assert result.battery_level is None
    assert result.connected is True  # set unconditionally on a successful fetch
    assert result.engine_on is None


# ---------------------------------------------------------------------------
# MAPPED_KEYS — used by diagnostics.py to tell mapped fields apart from
# ones the vehicle sends but no entity uses yet. These tests exist so that
# adding a new mapped field to parameters_to_telemetry without updating
# MAPPED_KEYS gets caught here instead of silently breaking diagnostics.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [
        "soc",
        "driverDoor",
        "driverDoorLock",
        "lfTyrePressure",
        "highBeam",
        "ChrgSts",
        "totalOdometer",
    ],
)
def test_mapped_keys_contains_known_mapped_fields(key):
    assert key in telemetry.MAPPED_KEYS


@pytest.mark.parametrize(
    "key",
    [
        "skyWindowDegree",
        "driverSeatHeatStatus",
        "chargeCoverStatus",
        "steeringWheelHeating",
    ],
)
def test_mapped_keys_excludes_known_unmapped_fields(key):
    # These are documented in docs/telemetry-parameters.md as candidates
    # not implemented yet. If one of these starts failing, it means the
    # field was mapped in parameters_to_telemetry — update MAPPED_KEYS
    # (and this test) to match.
    assert key not in telemetry.MAPPED_KEYS


@pytest.mark.parametrize(
    "key",
    [
        "hoodStatus",
        "airStatus",
        "airConditioningHairRatings",
        "airConditioningSetTemperature",
        "totalMeterYesterday",
        "igniteCumulativeMileage",
        "leftFrontTireTemperature",
        "rightFrontTireTemperature",
        "leftRearTireTemperature",
        "rightRearTireTemperature",
    ],
)
def test_mapped_keys_contains_newly_mapped_fields(key):
    # Confirmed against the real vehicle on 2026-09-18 (see
    # docs/telemetry-parameters.md) and mapped in this same session.
    assert key in telemetry.MAPPED_KEYS


@pytest.mark.parametrize(
    "key",
    [
        # diverWindow/etc. duplicated front_left_door/etc. — removed
        # in v1.2.0.
        "diverWindow",
        "passengerWindow",
        "leftRearWindow",
        "rightRearWindow",
        # *WindowDegree fields report movement acceleration, not
        # window position — removed in v1.2.0.
        "leftAnteriorWindowDegree",
        "rightAnteriorWindowDegree",
        "leftRearWindowDegree",
        "rightRearWindowDegree",
    ],
)
def test_mapped_keys_excludes_fields_removed_in_v1_2_0(key):
    assert key not in telemetry.MAPPED_KEYS
