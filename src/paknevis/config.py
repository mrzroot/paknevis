"""Configuration model and loading from ``pyproject.toml`` / ``.paknevis.toml``.

Example ``pyproject.toml``::

    [tool.paknevis]
    disable = ["kashida"]
    digits = "persian"        # persian | latin | keep
    ezafe = "zwnj"            # zwnj | hamza
    teh-marbuta = "warn"      # warn | heh | teh
    exclude = ["vendor/**"]
    dictionaries = ["docs/words.yaml"]

    [tool.paknevis.severity]
    spelling = "error"

    [tool.paknevis.spelling]
    "وبسایت" = "وب‌سایت"
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from .models import Severity

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib

__all__ = ["CONFIG_FILENAMES", "Config", "ConfigError", "find_config_file", "load_config"]

DigitStyle = Literal["persian", "latin", "keep"]
EzafeStyle = Literal["zwnj", "hamza"]
TehMarbutaMode = Literal["warn", "heh", "teh"]

CONFIG_FILENAMES = (".paknevis.toml", "paknevis.toml", "pyproject.toml")

DEFAULT_EXCLUDE = (
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
)


class ConfigError(ValueError):
    """Raised when a configuration file or value is invalid."""


@dataclass(frozen=True)
class Config:
    """Immutable linter configuration.

    Rules may be referred to by name (``arabic-yeh``) or code (``PN101``)
    in :attr:`disable`, :attr:`enable` and :attr:`severity`; they are
    normalised to names by :meth:`resolved`.
    """

    disable: frozenset[str] = frozenset()
    enable: frozenset[str] = frozenset()
    digits: DigitStyle = "persian"
    ezafe: EzafeStyle = "zwnj"
    teh_marbuta: TehMarbutaMode = "warn"
    severity: tuple[tuple[str, Severity], ...] = ()
    spelling: tuple[tuple[str, str], ...] = ()
    dictionaries: tuple[str, ...] = ()
    latex_text_commands: tuple[str, ...] = ()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    extend_exclude: tuple[str, ...] = ()
    fail_on: Severity = Severity.WARNING
    root: Path | None = field(default=None, compare=False)

    # ------------------------------------------------------------------ #
    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, root: Path | None = None) -> Config:
        """Build a config from a mapping such as a ``[tool.paknevis]`` table.

        Keys may use dashes or underscores. Unknown keys raise
        :class:`ConfigError` so typos are caught early.
        """
        kwargs: dict[str, Any] = {}
        for raw_key, value in data.items():
            key = raw_key.replace("-", "_")
            if key not in _KNOWN_KEYS:
                known = ", ".join(sorted(k.replace("_", "-") for k in _KNOWN_KEYS))
                raise ConfigError(f"unknown paknevis option {raw_key!r} (known: {known})")
            kwargs[key] = _convert(key, value)
        return cls(root=root, **kwargs)

    def merged(self, **overrides: Any) -> Config:
        """Return a copy with *overrides* applied (``None`` values are ignored)."""
        clean: dict[str, Any] = {}
        for key, value in overrides.items():
            if value is None:
                continue
            if key in _KNOWN_KEYS:
                value = _convert(key, value)
            clean[key] = value
        return replace(self, **clean)

    def severity_for(self, name: str, code: str, default: Severity) -> Severity:
        """Return the effective severity for a rule."""
        for key, value in self.severity:
            if key in (name, code):
                return value
        return default

    def spelling_entries(self) -> dict[str, str]:
        """Return extra spelling corrections from config and dictionary files."""
        from .dictionary import load_dictionary_file

        entries: dict[str, str] = {}
        base = self.root or Path.cwd()
        for name in self.dictionaries:
            path = Path(name)
            if not path.is_absolute():
                path = base / path
            entries.update(load_dictionary_file(path))
        entries.update(dict(self.spelling))
        return entries


def _as_str_tuple(key: str, value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    if not isinstance(value, Iterable) or not all(isinstance(v, str) for v in value):
        raise ConfigError(f"option {key!r} must be a list of strings")
    return tuple(value)


def _choice(key: str, value: Any, choices: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value.lower() not in choices:
        raise ConfigError(f"option {key!r} must be one of {', '.join(choices)} (got {value!r})")
    return value.lower()


def _convert(key: str, value: Any) -> Any:
    if key in ("disable", "enable"):
        return frozenset(_as_str_tuple(key, value))
    if key in ("dictionaries", "latex_text_commands", "include", "exclude", "extend_exclude"):
        return _as_str_tuple(key, value)
    if key == "digits":
        return _choice(key, value, ("persian", "latin", "keep"))
    if key == "ezafe":
        return _choice(key, value, ("zwnj", "hamza"))
    if key == "teh_marbuta":
        return _choice(key, value, ("warn", "heh", "teh"))
    if key == "fail_on":
        try:
            return Severity.parse(value)
        except (ValueError, AttributeError) as exc:
            raise ConfigError(f"option 'fail-on': {exc}") from None
    if key == "severity":
        if isinstance(value, tuple):
            return value
        if not isinstance(value, Mapping):
            raise ConfigError("option 'severity' must be a table of rule = severity")
        try:
            return tuple((str(k), Severity.parse(v)) for k, v in value.items())
        except (ValueError, AttributeError) as exc:
            raise ConfigError(f"option 'severity': {exc}") from None
    if key == "spelling":
        if isinstance(value, tuple):
            return value
        if not isinstance(value, Mapping) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in value.items()
        ):
            raise ConfigError("option 'spelling' must be a table of wrong = right strings")
        return tuple(value.items())
    raise AssertionError(key)  # pragma: no cover


_KNOWN_KEYS = frozenset(
    {
        "disable",
        "enable",
        "digits",
        "ezafe",
        "teh_marbuta",
        "severity",
        "spelling",
        "dictionaries",
        "latex_text_commands",
        "include",
        "exclude",
        "extend_exclude",
        "fail_on",
    }
)


def find_config_file(start: Path) -> Path | None:
    """Search *start* and its parents for a paknevis configuration file.

    ``pyproject.toml`` only counts if it contains a ``[tool.paknevis]`` table.
    """
    start = start.resolve()
    directory = start if start.is_dir() else start.parent
    for folder in (directory, *directory.parents):
        for name in CONFIG_FILENAMES:
            candidate = folder / name
            if not candidate.is_file():
                continue
            if name == "pyproject.toml" and "paknevis" not in _read_toml(candidate).get("tool", {}):
                continue
            return candidate
    return None


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            data: dict[str, Any] = tomllib.load(handle)
            return data
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: invalid TOML: {exc}") from None


def load_config(path: Path | None = None, *, start: Path | None = None) -> Config:
    """Load configuration from *path*, or discover it upwards from *start*.

    Returns a default :class:`Config` if no configuration file is found.
    """
    if path is None:
        path = find_config_file(start or Path.cwd())
        if path is None:
            return Config(root=(start or Path.cwd()).resolve())
    data = _read_toml(path)
    if path.name == "pyproject.toml" or "tool" in data:
        data = data.get("tool", {}).get("paknevis", {})
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: [tool.paknevis] must be a table")
    try:
        return Config.from_mapping(data, root=path.parent.resolve())
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from None
