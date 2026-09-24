"""Unit tests for sensor.py's pure logic.

sensor.py imports homeassistant.components.sensor, which isn't
installed in this test environment (unlike aiohttp for api.py — see
lint.yaml — adding the full homeassistant package as a CI dependency
just for this one pure function would be a much heavier change than
warranted). Instead, this extracts just the pure, HA-free part of the
module — the CHARGE_STATUS_* constants and _charge_status() — by
slicing the source text and exec'ing it in an isolated namespace, the
same technique used to validate coordinator.py's pure helpers
throughout development.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.deepal_spain_dec.models import DeepalTelemetry

_SENSOR_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "deepal_spain_dec"
    / "sensor.py"
)


def _load_charge_status_logic() -> dict:
    """Exec just the CHARGE_STATUS_*/_charge_status part of sensor.py."""
    source = _SENSOR_PY.read_text()
    start = source.index("CHARGE_STATUS_DISCONNECTED = ")
    end = source.index("SENSOR_DESCRIPTIONS: tuple[")

    namespace = {"DeepalTelemetry": DeepalTelemetry}
    exec(source[start:end], namespace)  # noqa: S102 - trusted, local file

    return namespace


_LOGIC = _load_charge_status_logic()
_charge_status = _LOGIC["_charge_status"]
DISCONNECTED = _LOGIC["CHARGE_STATUS_DISCONNECTED"]
CONNECTED_AC = _LOGIC["CHARGE_STATUS_CONNECTED_AC"]
CONNECTED_DC = _LOGIC["CHARGE_STATUS_CONNECTED_DC"]
CHARGING_AC = _LOGIC["CHARGE_STATUS_CHARGING_AC"]
CHARGING_DC = _LOGIC["CHARGE_STATUS_CHARGING_DC"]


def _telemetry(
    *,
    ac: bool | None,
    dc: bool | None,
    charging: bool | None,
) -> DeepalTelemetry:
    return DeepalTelemetry(
        ac_charge_connector_connected=ac,
        dc_charge_connector_connected=dc,
        charging=charging,
    )


@pytest.mark.parametrize(
    ("ac", "dc", "charging", "expected"),
    [
        # The five cases exactly as specified by the user.
        (False, False, False, DISCONNECTED),
        (True, False, False, CONNECTED_AC),
        (False, True, False, CONNECTED_DC),
        (True, False, True, CHARGING_AC),
        (False, True, True, CHARGING_DC),
    ],
)
def test_charge_status_specified_cases(ac, dc, charging, expected):
    assert (
        _charge_status(_telemetry(ac=ac, dc=dc, charging=charging))
        == expected
    )


@pytest.mark.parametrize(
    ("ac", "dc", "charging"),
    [
        (None, False, False),
        (False, None, False),
        (False, False, None),
    ],
)
def test_charge_status_unknown_input_is_unknown(ac, dc, charging):
    # Any unknown underlying value means an unconfident guess — the
    # sensor shows "unknown" rather than a specific, possibly wrong,
    # label.
    assert (
        _charge_status(_telemetry(ac=ac, dc=dc, charging=charging))
        is None
    )


def test_charge_status_charging_without_a_known_connector_is_unknown():
    # Physically shouldn't happen (charging implies a connector is in),
    # but telemetry can lag — don't invent a label for a combination
    # the user's specification doesn't cover.
    assert (
        _charge_status(_telemetry(ac=False, dc=False, charging=True))
        is None
    )


def test_charge_status_both_connectors_prefers_ac():
    # Both connectors reporting plugged in at once shouldn't happen on
    # the real vehicle, but the evaluation order (AC checked before
    # DC) still resolves it deterministically rather than raising.
    assert (
        _charge_status(_telemetry(ac=True, dc=True, charging=False))
        == CONNECTED_AC
    )
