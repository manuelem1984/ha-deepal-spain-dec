"""Unit tests for the "dec:" custom icon set (icons/dec-icons.js).

Pure Python/XML checks — no Node.js involved (not installed in CI; see
lint.yaml). What actually matters is verified directly with Node
during development (see icons/README.md and the commit that added
this), including running the real script and calling
window.customIconsets["dec"](...).

Two categories of icon, checked differently:
- "Simple" icons (steering-wheel-heat, the arrow-circle-* turn
  signals): plain Iconify SVGs with exactly one meaningful <path>.
  For these, dec-icons.js's entry must match that path/viewBox
  exactly — protects against the two files drifting apart.
- "Reconstructed" icons (car-light-*): their source .svg is an
  animated line-md icon (SMIL <animate> inside an SVG <mask>),
  incompatible with our simple static {path, viewBox} format. The
  dec-icons.js entry for these is a manually computed static
  approximation (a shared lamp-housing shape plus filled capsule
  shapes standing in for the animated light rays / off-slash),
  verified visually with a real headless-browser screenshot during
  development — not something a source-SVG text comparison can
  check. What's verified here instead: every expected reconstructed
  icon exists, shares the same lamp-housing sub-path (so the on/off/
  dimmed/full/parking variants stay visually consistent with each
  other), and its path data is at least well-formed.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_ICONS_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "deepal_spain_dec"
    / "icons"
)
_SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

# Shared lamp-housing shape every car-light-* icon is built from —
# see icons/README.md for how these were derived from the original
# line-md animated SVGs.
_CAR_LIGHT_BODY_PATH = (
    "M21 12c0 -3.31 -3.5 -6.25 -8.25 -6.25c-0.5 0 -1.75 2.75 -1.75 "
    "6.25c0 3.5 1.25 6.25 1.75 6.25c4.75 0 8.25 -2.94 8.25 -6.25Z"
)
_RECONSTRUCTED_ICONS = {
    "car-light-full-on",
    "car-light-full-off",
    "car-light-dimmed-on",
    "car-light-dimmed-off",
    "car-light-parking-on",
    "car-light-parking-off",
}


def _real_path_and_viewbox(svg_path: Path) -> tuple[str, str]:
    """Extract the meaningful path's `d` and the root `viewBox`.

    These Iconify SVGs have two <path> elements: an invisible
    full-canvas rectangle (fill="none", padding trick) and the actual
    glyph (fill="currentColor"). Only the latter matters. Only valid
    for "simple" icons — see module docstring.
    """
    root = ET.parse(svg_path).getroot()
    paths = root.findall("svg:path", _SVG_NS)
    real_path = next(
        p for p in paths if p.get("fill") == "currentColor"
    )
    return real_path.get("d"), root.get("viewBox")


def _load_icons_object() -> dict:
    """Parse the `const icons = {...}` object out of dec-icons.js.

    A pure text/JSON extraction — the object literal in the generated
    file is plain JSON (see frontend_icons.py generation logic), so
    this doesn't need a JS parser.
    """
    source = (_ICONS_DIR / "dec-icons.js").read_text(encoding="utf-8")
    match = re.search(
        r"const icons = (\{.*?\n\});", source, re.DOTALL
    )
    assert match, "no se encontró 'const icons = {...};' en dec-icons.js"
    return json.loads(match.group(1))


_ALL_SVG_FILES = sorted(_ICONS_DIR.glob("*.svg"))
_SIMPLE_SVG_FILES = [
    p for p in _ALL_SVG_FILES if p.stem not in _RECONSTRUCTED_ICONS
]


def test_icons_directory_has_at_least_one_svg():
    assert _ALL_SVG_FILES, "icons/ no contiene ningún .svg"


@pytest.mark.parametrize(
    "svg_path", _SIMPLE_SVG_FILES, ids=lambda p: p.stem
)
def test_simple_svg_has_exactly_two_paths_one_visible(svg_path):
    root = ET.parse(svg_path).getroot()
    paths = root.findall("svg:path", _SVG_NS)
    visible = [p for p in paths if p.get("fill") == "currentColor"]
    assert len(visible) == 1, (
        f"{svg_path.name}: se esperaba exactamente un <path> con "
        f"fill=currentColor, hay {len(visible)}"
    )


@pytest.mark.parametrize(
    "svg_path", _SIMPLE_SVG_FILES, ids=lambda p: p.stem
)
def test_simple_svg_matches_dec_icons_js_entry(svg_path):
    icons = _load_icons_object()
    icon_name = svg_path.stem

    assert icon_name in icons, (
        f"{svg_path.name} no tiene entrada correspondiente en "
        "dec-icons.js — regenerar el script (ver icons/README.md)"
    )

    expected_path, expected_view_box = _real_path_and_viewbox(
        svg_path
    )
    entry = icons[icon_name]

    assert entry["path"] == expected_path
    assert entry["viewBox"] == expected_view_box


@pytest.mark.parametrize(
    "icon_name", sorted(_RECONSTRUCTED_ICONS)
)
def test_reconstructed_car_light_icon_exists_and_is_well_formed(
    icon_name,
):
    icons = _load_icons_object()

    assert icon_name in icons, (
        f"falta la entrada reconstruida '{icon_name}' en dec-icons.js"
    )

    entry = icons[icon_name]
    assert entry["viewBox"] == "0 0 24 24"
    assert entry["path"].startswith("M")
    assert entry["path"].endswith("Z")
    # Todas comparten la misma carcasa de luz, para que las variantes
    # (full/dimmed/parking, on/off) se vean visualmente coherentes
    # entre sí — ver icons/README.md.
    assert _CAR_LIGHT_BODY_PATH in entry["path"]


def test_dec_icons_js_has_no_extra_entries_without_a_source_svg():
    icons = _load_icons_object()
    svg_names = {p.stem for p in _ALL_SVG_FILES}

    assert set(icons) == svg_names, (
        "dec-icons.js tiene entradas sin un .svg de origen "
        f"correspondiente: {set(icons) - svg_names}"
    )
