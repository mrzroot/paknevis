"""The playground bundle in docs/ must match the package source exactly."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_builder():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("build_playground", ROOT / "scripts" / "build_playground.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_playground"] = module
    spec.loader.exec_module(module)
    return module


def test_bundle_is_up_to_date() -> None:
    builder = _load_builder()
    assert builder.TARGET.exists(), "run: python scripts/build_playground.py"
    assert builder.bundle_files() == builder.package_files(), "stale bundle; run: python scripts/build_playground.py"


def test_manifest_version_matches() -> None:
    import paknevis

    manifest = json.loads((ROOT / "docs" / "assets" / "py" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == paknevis.__version__


def test_playground_references_bundle_and_font() -> None:
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "docs" / "assets" / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "assets" / "style.css").read_text(encoding="utf-8")
    assert "assets/py/paknevis.zip" in js
    assert "paknevis.web" in js
    assert "Vazirmatn-wght.woff2" in css
    assert (ROOT / "docs" / "assets" / "fonts" / "Vazirmatn-wght.woff2").exists()
    assert 'dir="rtl"' in html
