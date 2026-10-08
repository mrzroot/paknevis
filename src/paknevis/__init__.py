"""paknevis (پاک‌نویس) — a linter and auto-fixer for Persian text.

Quick start::

    >>> import paknevis
    >>> paknevis.fix("كتاب هاي من")
    'کتاب‌های من'
    >>> [d.rule for d in paknevis.lint("علي")]
    ['arabic-yeh']

Both functions accept ``syntax`` (``"plain"``, ``"markdown"``, ``"html"`` or
``"latex"``) so that code, URLs, markup and math are never modified, plus a
:class:`Config` or keyword overrides such as ``digits="latin"`` or
``disable=["kashida"]``.
"""

from __future__ import annotations

from typing import Any

from ._version import __version__
from .config import Config, ConfigError, load_config
from .engine import FixResult, Linter, get_linter
from .formats import SYNTAXES, detect_syntax
from .models import Diagnostic, Severity
from .rules import ALL_RULES, Rule, get_rule

__all__ = [
    "ALL_RULES",
    "SYNTAXES",
    "Config",
    "ConfigError",
    "Diagnostic",
    "FixResult",
    "Linter",
    "Rule",
    "Severity",
    "__version__",
    "detect_syntax",
    "fix",
    "get_rule",
    "lint",
    "load_config",
]


def _linter(config: Config | None, options: dict[str, Any]) -> Linter:
    base = config or Config()
    return get_linter(base.merged(**options) if options else base)


def lint(text: str, *, syntax: str = "plain", config: Config | None = None, **options: Any) -> list[Diagnostic]:
    """Lint *text* and return a list of :class:`Diagnostic` sorted by position.

    Args:
        text: The text to check.
        syntax: ``"plain"``, ``"markdown"``, ``"html"`` or ``"latex"``
            (aliases such as ``"md"`` and ``"tex"`` work too).
        config: Optional :class:`Config`; defaults to the built-in defaults.
        **options: Config overrides, e.g. ``digits="latin"``.
    """
    return _linter(config, options).lint(text, syntax=syntax)


def fix(text: str, *, syntax: str = "plain", config: Config | None = None, **options: Any) -> str:
    """Return *text* with all safe fixes applied.

    The result is idempotent: ``fix(fix(x)) == fix(x)``. Protected regions
    (code, URLs, e-mails, markup, math, front matter) are returned unchanged.
    """
    return _linter(config, options).fix(text, syntax=syntax)
