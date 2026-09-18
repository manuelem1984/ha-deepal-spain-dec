"""Pytest configuration shared by all tests.

telemetry.py and models.py are pure Python (no Home Assistant imports),
but they live inside a package whose __init__.py *does* import
homeassistant.* — and Home Assistant is not installed in this test
environment (these tests must run without a real HA instance or a car).

To import telemetry.py without triggering that __init__.py, we register
lightweight stand-in packages in sys.modules with __path__ pointing at
the real directories. Python's import system then finds and imports the
real telemetry.py / models.py files normally (relative imports and all),
without ever executing custom_components/deepal_spain_dec/__init__.py.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CUSTOM_COMPONENTS_DIR = REPO_ROOT / "custom_components"
COMPONENT_DIR = CUSTOM_COMPONENTS_DIR / "deepal_spain_dec"


def _register_stub_package(name: str, path: Path) -> None:
    """Register an empty package pointing at `path`, if not already done."""
    if name in sys.modules:
        return

    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


_register_stub_package("custom_components", CUSTOM_COMPONENTS_DIR)
_register_stub_package("custom_components.deepal_spain_dec", COMPONENT_DIR)
