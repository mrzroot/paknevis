from __future__ import annotations

import paknevis

Z = "\u200c"


def fixed_by(rule: str, text: str, **options: object) -> str:
    """Fix *text* with only *rule* enabled."""
    others = [r.name for r in paknevis.ALL_RULES if r.name != rule]
    return paknevis.fix(text, disable=others, **options)


def rules_hit(text: str, **options: object) -> set[str]:
    return {d.rule for d in paknevis.lint(text, **options)}
