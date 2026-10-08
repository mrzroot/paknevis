"""Bundle the paknevis package for the in-browser playground (docs/assets/py/).

The playground runs the *real* Python package under Pyodide. This script zips
``src/paknevis`` into ``docs/assets/py/paknevis.zip``; the test-suite fails if
the bundle is out of date, so CI guarantees the playground matches the source.

Usage::

    python scripts/build_playground.py          # rebuild
    python scripts/build_playground.py --check  # exit 1 if stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "paknevis"
TARGET = ROOT / "docs" / "assets" / "py" / "paknevis.zip"
MANIFEST = TARGET.with_name("manifest.json")
SUFFIXES = {".py", ".yaml", ".typed"}


def package_files() -> dict[str, bytes]:
    """Map archive names (``paknevis/...``) to file contents."""
    files: dict[str, bytes] = {}
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file() and path.suffix in SUFFIXES and "__pycache__" not in path.parts:
            files[path.relative_to(SOURCE.parent).as_posix()] = path.read_bytes()
    return files


def bundle_files(path: Path = TARGET) -> dict[str, bytes]:
    """Read the files contained in an existing bundle."""
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def version() -> str:
    namespace: dict[str, str] = {}
    exec((SOURCE / "_version.py").read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


def build() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    files = package_files()
    with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    digest = hashlib.sha256(b"".join(name.encode() + data for name, data in files.items())).hexdigest()
    MANIFEST.write_text(
        json.dumps({"version": version(), "files": len(files), "sha256": digest}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the bundle is stale")
    args = parser.parse_args()
    if args.check:
        if not TARGET.exists() or bundle_files() != package_files():
            print(f"{TARGET.relative_to(ROOT)} is stale; run: python scripts/build_playground.py")
            return 1
        print("playground bundle is up to date")
        return 0
    build()
    print(f"wrote {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
