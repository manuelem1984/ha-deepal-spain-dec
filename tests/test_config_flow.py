"""Unit tests for config_flow.py's PIN validation logic.

config_flow.py imports several Home Assistant modules (voluptuous
selectors, config_entries) not installed in this test environment —
see tests/test_sensor.py for why the same source-extraction technique
is used instead of adding the full homeassistant package as a CI
dependency. Only _async_validate_pin_block() is pure enough (given a
fake coordinator) to exercise this way.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from custom_components.deepal_spain_dec.api_errors import (
    DeepalApiError,
    DeepalRateLimitError,
)
from custom_components.deepal_spain_dec.const import (
    CONF_CONTROL_PIN,
    CONF_PIN_ENABLED,
    DOMAIN,
)

_CONFIG_FLOW_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "deepal_spain_dec"
    / "config_flow.py"
)


def _load_validate_pin_block():
    """Exec just the _async_validate_pin_block() method as a plain function."""
    source = _CONFIG_FLOW_PY.read_text()
    start = source.index(
        "    async def _async_validate_pin_block("
    )
    method_source = "class _Fake:\n" + source[start:]

    namespace = {
        "DOMAIN": DOMAIN,
        "CONF_PIN_ENABLED": CONF_PIN_ENABLED,
        "CONF_CONTROL_PIN": CONF_CONTROL_PIN,
        "DeepalApiError": DeepalApiError,
        "DeepalRateLimitError": DeepalRateLimitError,
        "Any": Any,
    }
    exec(method_source, namespace)  # noqa: S102 - trusted, local file

    return namespace["_Fake"]._async_validate_pin_block


_async_validate_pin_block = _load_validate_pin_block()


class _FakeCoordinator:
    """Stands in for hass.data[DOMAIN][entry_id]; only .api is used."""

    def __init__(self, outcome):
        self.api = self
        self._outcome = outcome

    async def check_control_code(self, control_pin):
        if self._outcome == "ok":
            return "rc-token"
        raise self._outcome


class _FakeOptionsFlow:
    """Stands in for the OptionsFlow instance _async_validate_pin_block runs on."""

    def __init__(self, outcome):
        self.hass = type(
            "_Hass",
            (),
            {"data": {DOMAIN: {"entry-1": _FakeCoordinator(outcome)}}},
        )()
        self.config_entry = type(
            "_Entry", (), {"entry_id": "entry-1"}
        )()


def test_pin_block_disabled_skips_validation_entirely():
    async def run():
        result = await _async_validate_pin_block(
            _FakeOptionsFlow("ok"),
            {CONF_PIN_ENABLED: False},
        )
        assert result == {}

    asyncio.run(run())


def test_pin_block_enabled_without_pin_value():
    async def run():
        result = await _async_validate_pin_block(
            _FakeOptionsFlow("ok"),
            {CONF_PIN_ENABLED: True, CONF_CONTROL_PIN: ""},
        )
        assert result == {"base": "pin_required"}

    asyncio.run(run())


def test_pin_block_enabled_with_valid_pin():
    async def run():
        result = await _async_validate_pin_block(
            _FakeOptionsFlow("ok"),
            {CONF_PIN_ENABLED: True, CONF_CONTROL_PIN: "1234"},
        )
        assert result == {}

    asyncio.run(run())


def test_pin_block_enabled_with_invalid_pin():
    async def run():
        result = await _async_validate_pin_block(
            _FakeOptionsFlow(DeepalApiError("bad pin")),
            {CONF_PIN_ENABLED: True, CONF_CONTROL_PIN: "0000"},
        )
        assert result == {"base": "pin_invalid"}

    asyncio.run(run())


def test_pin_block_enabled_when_rate_limited():
    async def run():
        result = await _async_validate_pin_block(
            _FakeOptionsFlow(DeepalRateLimitError("locked out")),
            {CONF_PIN_ENABLED: True, CONF_CONTROL_PIN: "1234"},
        )
        assert result == {"base": "pin_rate_limited"}

    asyncio.run(run())
