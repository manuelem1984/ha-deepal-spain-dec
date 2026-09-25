"""Unit tests for coordinator.py's pure logic.

coordinator.py imports homeassistant.helpers.update_coordinator and
several other Home Assistant modules, none of which are installed in
this test environment (see tests/test_sensor.py for why the same
extraction technique is used instead of adding the full homeassistant
package as a CI dependency).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

_COORDINATOR_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "deepal_spain_dec"
    / "coordinator.py"
)


def _load_arming_decision() -> dict:
    """Exec just the pure _is_command_blocked_by_arming() function."""
    source = _COORDINATOR_PY.read_text()
    start = source.index("_COMMAND_RESULT_TIMEOUT")
    end = source.index("class DeepalSpainCoordinator")

    namespace = {"Any": Any, "PIN_MODE_SAFE": "safe"}
    exec(source[start:end], namespace)  # noqa: S102 - trusted, local file

    return namespace


_LOGIC = _load_arming_decision()
_is_command_blocked_by_arming = _LOGIC["_is_command_blocked_by_arming"]


@pytest.mark.parametrize(
    ("pin_mode", "is_armed", "requires_arming", "expected_blocked"),
    [
        # "Opción A" (unsafe): never blocks, armed or not.
        ("unsafe", False, True, False),
        ("unsafe", True, True, False),
        # "Opción B" (safe): blocks unless armed.
        ("safe", False, True, True),
        ("safe", True, True, False),
        # A command that doesn't opt in is never blocked, whatever
        # the mode.
        ("safe", False, False, False),
        ("unsafe", False, False, False),
    ],
)
def test_is_command_blocked_by_arming(
    pin_mode,
    is_armed,
    requires_arming,
    expected_blocked,
):
    assert (
        _is_command_blocked_by_arming(
            pin_mode=pin_mode,
            is_armed=is_armed,
            requires_arming=requires_arming,
        )
        is expected_blocked
    )
