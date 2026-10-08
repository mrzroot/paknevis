"""JSON bridge used by the in-browser playground (running under Pyodide).

Kept in the package (and tested) so that the playground exercises exactly the
same code paths as the library and CLI.
"""

from __future__ import annotations

import difflib
import json
from typing import Any

from . import __version__
from .config import Config
from .engine import get_linter
from .rules import ALL_RULES


def rules_json() -> str:
    """Return metadata for all rules as JSON."""
    return json.dumps(
        [
            {
                "code": rule.code,
                "name": rule.name,
                "category": rule.category,
                "severity": rule.severity.value,
                "fixable": rule.fixable,
                "title_en": rule.title_en,
                "title_fa": rule.title_fa,
                "description_en": rule.description_en,
                "description_fa": rule.description_fa,
                "examples": [[e.before, e.after] for e in rule.examples],
            }
            for rule in sorted(ALL_RULES, key=lambda r: r.code)
        ],
        ensure_ascii=False,
    )


def run(text: str, options_json: str = "{}") -> str:
    """Lint and fix *text*; return ``{"version", "fixed", "diagnostics", "changes"}`` as JSON.

    ``options_json`` may contain ``syntax``, ``digits``, ``ezafe``,
    ``teh_marbuta`` and ``disable`` (a list of rule names). ``changes`` lists
    ``[fixed_start, fixed_end, original_start, original_end]`` code-point
    ranges that differ between the original and the fixed text.
    """
    options: dict[str, Any] = json.loads(options_json or "{}")
    syntax = options.pop("syntax", "plain")
    config = Config.from_mapping({k: v for k, v in options.items() if v is not None})
    linter = get_linter(config)
    diagnostics = linter.lint(text, syntax=syntax)
    fixed = linter.fix(text, syntax=syntax)
    return json.dumps(
        {
            "version": __version__,
            "fixed": fixed,
            "diagnostics": [d.to_dict() for d in diagnostics],
            "changes": changes(text, fixed),
        },
        ensure_ascii=False,
    )


def changes(original: str, fixed: str) -> list[list[int]]:
    """Ranges that differ: ``[fixed_start, fixed_end, original_start, original_end]``."""
    if original == fixed:
        return []
    matcher = difflib.SequenceMatcher(a=original, b=fixed, autojunk=False)
    return [[j1, j2, i1, i2] for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
