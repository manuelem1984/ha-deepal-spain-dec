"""Unit tests for the "dec:" custom icon set (icons/dec-icons.js).

Pure Python/XML checks — no Node.js involved (not installed in CI; see
lint.yaml). What actually matters is verified directly with Node
during development (see icons/README.md and the commit that added
this), including running the real script and calling
window.customIconsets["dec"](...). What this test suite protects
against going forward is the two files drifting apart: every .svg in
icons/ should have a matching, correct entry in dec-icons.js.
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


def _real_path_and_viewbox(svg_path: Path) -> tuple[str, str]:
    """Extract the meaningful path's `d` and the root `viewBox`.

    These Iconify SVGs have two <path> elements: an invisible
    full-canvas rectangle (fill="none", padding trick) and the actual
    glyph (fill="currentColor"). Only the latter matters.
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


_SVG_FILES = sorted(_ICONS_DIR.glob("*.svg"))


def test_icons_directory_has_at_least_one_svg():
    assert _SVG_FILES, "icons/ no contiene ningún .svg"


@pytest.mark.parametrize(
    "svg_path", _SVG_FILES, ids=lambda p: p.stem
)
def test_svg_has_exactly_two_paths_one_visible(svg_path):
    root = ET.parse(svg_path).getroot()
    paths = root.findall("svg:path", _SVG_NS)
    visible = [p for p in paths if p.get("fill") == "currentColor"]
    assert len(visible) == 1, (
        f"{svg_path.name}: se esperaba exactamente un <path> con "
        f"fill=currentColor, hay {len(visible)}"
    )


@pytest.mark.parametrize(
    "svg_path", _SVG_FILES, ids=lambda p: p.stem
)
def test_svg_matches_dec_icons_js_entry(svg_path):
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


def test_dec_icons_js_has_no_extra_entries_without_a_source_svg():
    icons = _load_icons_object()
    svg_names = {p.stem for p in _SVG_FILES}

    assert set(icons) == svg_names, (
        "dec-icons.js tiene entradas sin un .svg de origen "
        f"correspondiente: {set(icons) - svg_names}"
    )
