"""Loading of spelling dictionaries (YAML).

A dictionary file is either a YAML mapping (``wrong: right``) or a list of
entries with ``wrong``/``right`` keys and an optional ``note``::

    - wrong: اطاق
      right: اتاق
      note: Standard spelling per the Academy of Persian Language.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

__all__ = ["DictionaryError", "builtin_dictionary", "load_dictionary_file", "parse_dictionary"]


class DictionaryError(ValueError):
    """Raised when a dictionary file is malformed."""


def parse_dictionary(data: Any, *, source: str = "<dictionary>") -> dict[str, str]:
    """Validate parsed YAML *data* and return a ``{wrong: right}`` mapping."""
    if data is None:
        return {}
    entries: dict[str, str] = {}
    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = []
        for index, item in enumerate(data):
            if not isinstance(item, dict) or "wrong" not in item or "right" not in item:
                raise DictionaryError(f"{source}: entry #{index + 1} needs 'wrong' and 'right' keys")
            items.append((item["wrong"], item["right"]))
    else:
        raise DictionaryError(f"{source}: expected a mapping or a list of entries")
    for wrong, right in items:
        if not isinstance(wrong, str) or not isinstance(right, str) or not wrong.strip():
            raise DictionaryError(f"{source}: entries must be non-empty strings ({wrong!r})")
        entries[wrong.strip()] = right.strip()
    return entries


def load_dictionary_file(path: Path) -> dict[str, str]:
    """Load a user dictionary from *path*."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DictionaryError(f"cannot read dictionary {path}: {exc.strerror}") from None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise DictionaryError(f"{path}: invalid YAML: {exc}") from None
    return parse_dictionary(data, source=str(path))


@lru_cache(maxsize=1)
def builtin_entries() -> tuple[dict[str, Any], ...]:
    """Return the raw built-in dictionary entries (with notes)."""
    text = resources.files("paknevis").joinpath("data/spelling.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    parse_dictionary(data, source="paknevis/data/spelling.yaml")  # validate
    return tuple(data)


def builtin_dictionary() -> dict[str, str]:
    """Return the curated built-in ``{wrong: right}`` dictionary."""
    return {entry["wrong"]: entry["right"] for entry in builtin_entries()}
