"""Static checks on the entity descriptions in sensor.py/binary_sensor.py.

Those modules import Home Assistant, which is not installed in the test
environment, so they are checked as source text instead: every `key=`
must be unique within its platform (it becomes part of the entity's
unique_id — a duplicate would silently drop an entity), and every
description must carry a `name=` and an icon or a device class.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_COMPONENT = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "deepal_spain_dec"
)

_DESCRIPTION = re.compile(
    r"Deepal(?:Binary)?SensorDescription\((.*?)\n    \),",
    re.DOTALL,
)


def _descriptions(filename: str) -> list[str]:
    source = (_COMPONENT / filename).read_text()
    return _DESCRIPTION.findall(source)


@pytest.mark.parametrize("filename", ["sensor.py", "binary_sensor.py"])
def test_keys_are_unique(filename):
    keys = [
        re.search(r'key="([a-z0-9_]+)"', block).group(1)
        for block in _descriptions(filename)
    ]
    assert keys, "no descriptions found — did the file change shape?"
    assert len(keys) == len(set(keys)), keys


@pytest.mark.parametrize("filename", ["sensor.py", "binary_sensor.py"])
def test_every_description_has_name_and_icon_or_device_class(filename):
    for block in _descriptions(filename):
        key = re.search(r'key="([a-z0-9_]+)"', block).group(1)
        assert 'name="' in block, key
        assert (
            "icon" in block or "device_class=" in block
        ), key


@pytest.mark.parametrize(
    ("filename", "key"),
    [
        ("sensor.py", "ac_charge_current"),
        ("sensor.py", "dc_charge_current"),
        ("sensor.py", "power_status"),
        ("binary_sensor.py", "any_door_open"),
        ("binary_sensor.py", "central_locking"),
        ("binary_sensor.py", "front_left_window"),
        ("binary_sensor.py", "front_right_window"),
        ("binary_sensor.py", "rear_left_window"),
        ("binary_sensor.py", "rear_right_window"),
        ("binary_sensor.py", "left_front_tire_alarm"),
        ("binary_sensor.py", "right_front_tire_alarm"),
        ("binary_sensor.py", "left_rear_tire_alarm"),
        ("binary_sensor.py", "right_rear_tire_alarm"),
    ],
)
def test_v1_3_1b13_entities_are_declared(filename, key):
    keys = {
        re.search(r'key="([a-z0-9_]+)"', block).group(1)
        for block in _descriptions(filename)
    }
    assert key in keys
